class DataBaseRouter:

    def db_for_read(self, model, **hints):
        if hasattr(model, "db_for_read"):
            return model.db_for_read(**hints)

    def db_for_write(self, model, **hints):
        if hasattr(model, "db_for_write"):
            return model.db_for_write(**hints)
