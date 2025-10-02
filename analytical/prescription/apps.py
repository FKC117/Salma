from django.apps import AppConfig


class PrescriptionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "prescription"
    verbose_name = 'Prescription Management System'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        # Temporarily disabled for initial testing
        # try:
        #     import prescription.signals
        # except ImportError:
        #     pass
        pass
