def informar(modelos, nombre, perfil):
    for clave_modelo, exactitud in modelos.items():
        print(f"{clave_modelo}: exactitud {exactitud:.3f}")
    print(f"{nombre}: listo")
    print("Perfil comprobado aparte:", perfil)
