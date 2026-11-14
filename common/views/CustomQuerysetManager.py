from django.conf import settings



class CustomQuerysetManager:
	CUSTOME_QUERYSET_MANAGER_CONFIG = {
		"model": 					None,
		"select_related_fields": 	(),
		"prefetch_related_fields":	()
	}


	def get_manager_name(self):
		# Read settings inside the method so dynamic setting overrides in tests work too
		if getattr(settings, "ACTIVE_ONLY", False):
			return "active_objects"
		elif getattr(settings, "CLOSEURE_PERIOD_INSTANCE_ID", None):
			return "specific_objects"
		return "objects"

	def get_manager(self, obj): return getattr(obj, self.get_manager_name())

	def get_queryset(self):
		if self.CUSTOME_QUERYSET_MANAGER_CONFIG['model'] is None:
			raise AssertionError("Subclasses must define 'model'.")

		manager_name = self.get_manager_name()
		manager = getattr(self.CUSTOME_QUERYSET_MANAGER_CONFIG['model'], manager_name)
		queryset = manager.all()

		if self.CUSTOME_QUERYSET_MANAGER_CONFIG['select_related_fields']:
			queryset = queryset.select_related(*self.CUSTOME_QUERYSET_MANAGER_CONFIG['select_related_fields'])

		if self.CUSTOME_QUERYSET_MANAGER_CONFIG['prefetch_related_fields']:
			queryset = queryset.prefetch_related(*self.CUSTOME_QUERYSET_MANAGER_CONFIG['prefetch_related_fields'])

		return queryset
