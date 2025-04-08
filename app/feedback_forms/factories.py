from factory import LazyAttribute, Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory

from app.feedback_forms.models import FeedbackForm, PathPattern


class FeedbackFormFactory(DjangoModelFactory):
    class Meta:
        model = FeedbackForm
        skip_postgeneration_save = True

    name = Sequence(lambda i: f"Test feedback form {i}")

    @post_generation
    def path_patterns(self, create, extracted, **kwargs):
        if extracted:
            for pattern in extracted:
                PathPatternFactory.create(feedback_form=self, pattern=pattern)


class PathPatternFactory(DjangoModelFactory):
    class Meta:
        model = PathPattern

    feedback_form = SubFactory(FeedbackFormFactory)
    project = LazyAttribute(lambda pattern: pattern.feedback_form.project)
    created_by = LazyAttribute(lambda pattern: pattern.feedback_form.created_by)
