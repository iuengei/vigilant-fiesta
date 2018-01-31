from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User, Group


@receiver(post_save, sender='main.Teacher')
def create_teacher_account(instance=None, created=False, update_fields=None, **kwargs):
    update_fields = update_fields if update_fields else []
    if created and instance.work_type == 1:

        email = instance.id_card[-6:] + '@jinghan.com'
        user = User.objects.create_user(email, instance.name, email)
        user.duty = 2
        user.branch = instance.branch
        user.teacher_info = instance
        user.save()

        user.groups.add(Group.objects.get(name='Teacher'))

    elif instance.work_type == 1 and 'work_type' in update_fields:
        email = instance.id_card[-6:] + '@jinghan.com'
        try:
            user = User.objects.get(teacher_info=instance)
            user.is_active = True
            user.save()
        except User.DoesNotExist:
            user = User.objects.create_user(email, instance.name, email)
            user.duty = 2
            user.branch = instance.branch
            user.teacher_info = instance
            user.save()
    elif 'work_type' in update_fields:
        user = User.objects.get(teacher_info=instance)
        user.is_active = False
        user.save()


@receiver(post_save, sender='main.Supervisor')
def create_supervisor_account(instance=None, created=False, **kwargs):
    if created:
        email = instance.id_card[-6:] + '@jinghan.com'
        user = User.objects.create_user(email, instance.name, email)
        user.duty = 1
        user.branch = instance.branch
        user.supervisor_info = instance
        user.save()

        user.groups.add(Group.objects.get(name='Supervisor'))
