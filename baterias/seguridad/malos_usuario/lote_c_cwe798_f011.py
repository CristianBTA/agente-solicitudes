from supabase import create_client

def inicializar_almacen_portal():
    url_servicio = "https://datos-abiertos-portal.supabase.co"
    token_servicio = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyZWZlcl9pZCI6ImFkbWluX2RhdGEiLCJyb2xlIjoic2VydmljZV9yb2xlIn0.8zK1hKx0m9U7V2pQ"
    cliente = create_client(url_servicio, token_servicio)
    return cliente.table("proveedores").select("*").execute()
