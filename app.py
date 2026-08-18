import streamlit as st
import requests
import csv
import io

# --- Configuración de la página ---
st.set_page_config(
    page_title="Exportador de Discord", 
    page_icon="🚀", 
    layout="centered"
)

# --- Elementos de la Interfaz ---
st.title("🚀 Exportador de Usuarios de Discord")
st.markdown("Descarga la lista de usuarios de tu servidor de Discord en formato CSV.")

# Intentamos obtener el token de los Secrets de Streamlit
try:
    TOKEN = st.secrets["DISCORD_TOKEN"]
except KeyError:
    st.error("⚠️ Falta configurar el DISCORD_TOKEN en los Secrets de Streamlit.")
    st.stop()

# --- Lógica de la API ---
def obtener_roles(guild_id):
    url = f"https://discord.com/api/v10/guilds/{guild_id}/roles"
    headers = {"Authorization": f"Bot {TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return {rol["id"]: rol["name"] for rol in res.json()}
    return {}

def generar_csv(guild_id):
    roles_map = obtener_roles(guild_id)
    headers = {"Authorization": f"Bot {TOKEN}"}
    miembros = []
    last_id = 0

    while True:
        url = f"https://discord.com/api/v10/guilds/{guild_id}/members?limit=1000&after={last_id}"
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            st.error(f"❌ ERROR {res.status_code}: Verifica el ID o los permisos de tu Bot.")
            return None

        data = res.json()
        if not data:
            break

        miembros.extend(data)
        last_id = data[-1]["user"]["id"]

    # Crear el CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Username", "Global Name", "UserID", "Nickname", "Roles"])

    for m in miembros:
        user = m.get("user", {})
        username = user.get("username", "")
        global_name = user.get("global_name", "") or "N/A"
        user_id = user.get("id", "")
        nickname = m.get("nick", "") or "N/A"

        nombres_roles = [roles_map.get(rid, rid) for rid in m.get("roles", [])]
        roles_str = ", ".join(nombres_roles)

        writer.writerow([username, global_name, user_id, nickname, roles_str])

    # Devolver los datos codificados en utf-8-sig (ideal para abrir en Excel sin que se rompan las tildes)
    return output.getvalue().encode('utf-8-sig'), len(miembros)

# --- Interfaz de Usuario ---
server_id_input = st.text_input("ID del Servidor (Guild ID)", placeholder="Ej: 123456789012345678")

if st.button("Buscar Usuarios", type="primary"):
    if not server_id_input.strip():
        st.warning("❌ Por favor, ingresa un ID válido.")
    else:
        with st.spinner("⏳ Conectando con Discord y procesando usuarios..."):
            resultado = generar_csv(server_id_input.strip())
            
            if resultado is not None:
                csv_bytes, cantidad = resultado
                st.success(f"✅ ¡Éxito! Se encontraron {cantidad} usuarios.")
                
                # Guardamos los bytes en el session_state para que el botón de descarga no recargue la página
                st.session_state['csv_data'] = csv_bytes
                st.session_state['guild_id'] = server_id_input.strip()

# Mostrar el botón de descarga si hay datos listos
if 'csv_data' in st.session_state:
    st.download_button(
        label="📥 Descargar CSV",
        data=st.session_state['csv_data'],
        file_name=f"Reporte_Usuarios_{st.session_state['guild_id']}.csv",
        mime="text/csv"
    )
