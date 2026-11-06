from pymongo import MongoClient

def conectar_coleccion_sensores():
    uri = "mongodb://sensor_writer:Pass4SensorCluster!@mongo01.internal:27017/telemetria"
    cliente = MongoClient(uri)
    return cliente.get_database()
