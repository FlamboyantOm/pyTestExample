from django.contrib.auth.models import User

class ApexUser(User):
    class Meta:
        permissions = (
            ("can_manage_cluster", "Upload Cluster"),
            ("can_manage_signature", "Upload Signature"),

            ("can_view_age", "Type Age View"),
            ("can_edit_age", "Type Age Edit"),
            ("can_approve_age", "Type Age Approve "),

            ("can_view_android", "Type Android View"),
            ("can_edit_android", "Type Android Edit"),
            ("can_approve_android", "Type Android Approve "),

            ("can_view_android_elf", "Type Android_Elf View"),
            ("can_edit_android_elf", "Type Android_Elf Edit"),
            ("can_approve_android_elf", "Type Android_Elf Approve "),

            ("can_view_vbs", "Type Vbs View"),
            ("can_edit_vbs", "Type Vbs Edit"),
            ("can_approve_vbs", "Type Vbs Approve "),

            ("can_view_auto_it", "Type Auto_It View"),
            ("can_edit_auto_it", "Type Auto_It Edit"),
            ("can_approve_auto_it", "Type Auto_It Approve "),

            ("can_view_elf", "Type Elf View"),
            ("can_edit_elf", "Type Elf Edit"),
            ("can_approve_elf", "Type Elf Approve "),

            ("can_view_eml", "Type Eml View"),
            ("can_edit_eml", "Edit Eml Edit"),
            ("can_approve_eml", "Type Eml Approve "),

            ("can_view_ole", "Type Ole View"),
            ("can_edit_ole", "Type Ole Edit"),
            ("can_approve_ole", "Type Ole Approve "),

            ("can_view_rtf", "Type Rtf View"),
            ("can_edit_rtf", "Type Rtf Edit"),
            ("can_approve_rtf", "Type Rtf Approve "),

            #state permission
            ("manager_state", "Manager State"),
            ("signature_manager_state", "Signature Manager State"),
            ("cluster_manager_state", "Cluster Manager State"),

            #role permission
            ("role_manager", "Role Manager"),
            ("role_reviewer", "Role Reviewer"),
            ("role_qa", "Role QA"),



        )



