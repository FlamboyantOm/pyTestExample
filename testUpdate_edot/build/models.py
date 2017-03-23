from django.db import models

# Create your models here.
class Capablities(models.Model):
    name = models.CharField(max_length=200,null=True)

    class Meta:
      db_table = "capablities"
      permissions = (
            ("can_create_build", "Create Normal Build"),
            ("can_create_revertbuild", "Create Revert Build"),
            ("can_view_buildhistory", "View Build History"),
            ("can_manage_buildengine", "Manage Build Engine"),
            ("can_view_statstics", "View Statstics"),
      )