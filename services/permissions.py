from rest_framework.permissions import DjangoModelPermissions


class CRUDPermission(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.create_%(model_name)s'],
        'PUT': ['%(app_label)s.update_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class AssociateCasePermission(DjangoModelPermissions):
    perms_map = {
        'POST': ['%(app_label)s.associate_cases'],
        'GET': ['%(app_label)s.associate_cases']
    }


class ViewPermission(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s']
    }


class RemoveCasePermission(DjangoModelPermissions):
    perms_map = {
        'POST': ['%(app_label)s.remove_case']
    }


class AssociateConfigPermission(DjangoModelPermissions):
    perms_map = {
        'POST': ['%(app_label)s.associate_config'],
        'GET': ['%(app_label)s.associate_config']
    }


class AssociateCounterPermission(DjangoModelPermissions):
    perms_map = {
        'POST': ['%(app_label)s.associate_counter'],
        'GET': ['%(app_label)s.associate_counter']
    }


class AssociateSetPermission(DjangoModelPermissions):
    perms_map = {
        'POST': ['%(app_label)s.associate_set'],
        'GET': ['%(app_label)s.associate_set']
    }


class RemoveSetsPermission(DjangoModelPermissions):
    perms_map = {
        'POST': ['%(app_label)s.remove_set']
    }


class RunnerPermission(DjangoModelPermissions):
    perms_map = {
        'POST': ['%(app_label)s.execute_%(model_name)s']
    }
