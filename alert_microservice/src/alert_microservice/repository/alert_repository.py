from alert_microservice.db_repository import MainRepository
from alert_microservice.interfaces import AbstractAlertClass
from alert_microservice.model.alert_model import Alert


class AlertRepository(MainRepository, AbstractAlertClass):

    def __init__(self, db):
        super().__init__(db, Alert)