import logging

def registrar_tramite_con_mascara(tipo_tramite, pasaporte):
    if len(pasaporte) > 4:
        mascara = pasaporte[:2] + ("*" * (len(pasaporte) - 4)) + pasaporte[-2:]
    else:
        mascara = "****"
    logging.info(f"Tramite {tipo_tramite} iniciado para documento {mascara}")
    return True
