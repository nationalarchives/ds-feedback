import time

from django.core.management.base import BaseCommand

from app.api.views import FeedbackFormPathPatternDetail
from app.feedback_forms.models import FeedbackForm, PathPattern
from app.projects.models import RETENTION_PERIOD_CHOICES, Project
from app.users.models import User


class Command(BaseCommand):
    help = "Tests the performance of feedback form lookup by path"

    def handle(self, *args, **options):
        user = User.objects.create(
            username="temp",
            password="password",
            is_staff=True,
            is_superuser=True,
        )
        projects = []
        feedback_forms = []
        path_patterns = []
        for project_index in range(10000):
            project = Project(
                created_by=user,
                name=project_index,
                domain="",
                retention_period_days=RETENTION_PERIOD_CHOICES[0],
                owned_by=user,
            )
            projects.append(project)

            for feedback_index in range(5):
                feedback_form = FeedbackForm(
                    name=feedback_index,
                    project=project,
                    created_by=user,
                )
                feedback_forms.append(feedback_form)

                for path_index in range(10):
                    path_pattern = PathPattern(
                        feedback_form=feedback_form,
                        project=project,
                        pattern=f"/path/{feedback_index}/{path_index}/",
                        is_wildcard=True,
                        created_by=user,
                    )
                    path_patterns.append(path_pattern)

        Project.objects.bulk_create(projects)
        FeedbackForm.objects.bulk_create(feedback_forms)
        PathPattern.objects.bulk_create(path_patterns)

        try:
            start = time.time()

            view = FeedbackFormPathPatternDetail()
            view.kwargs = {"path": "/path/1/2/3/", "project": projects[0].uuid}
            view.get_queryset().get()

            end = time.time()
            self.stdout.write(
                self.style.NOTICE(f"Took {(end - start) * 1000} milliseconds")
            )

        except Exception as error:
            self.stderr.write(self.style.ERROR(str(error)))

        PathPattern.objects.filter(created_by=user).delete()
        FeedbackForm.objects.filter(created_by=user).delete()
        Project.objects.filter(created_by=user).delete()
        user.delete()

        self.stdout.write(self.style.SUCCESS("Success"))
