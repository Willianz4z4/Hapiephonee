import pymongo
import dns.resolver

_original_init = dns.resolver.Resolver.__init__

def patched_init(self, *args, **kwargs):
    kwargs['configure'] = False
    _original_init(self, *args, **kwargs)
    self.nameservers = ['8.8.8.8', '8.8.4.4']

dns.resolver.Resolver.__init__ = patched_init

MONGO_URI = "mongodb+srv://termux_user:termuxkey@cluster0.<seu_codigo>.mongodb.net/?retryWrites=true&w=majority"

class TermuxReadOnlyDB:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    def obter_dados(self, nome_banco: str, nome_colecao: str, guild_id: str, modelo_celular: str = None):
        filtro = {"guild_id": str(guild_id)}
        if modelo_celular:
            filtro["report.system_info.model"] = modelo_celular
            
        return list(self.client[nome_banco][nome_colecao].find(filtro))

db_read = TermuxReadOnlyDB()
