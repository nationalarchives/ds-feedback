# Technical Guide

Start with [Key Concepts](./key-concepts.md) for an overview of concepts/terms.

## Data model

You can also explore the data model on the [Mermaid data model diagram](./data-model.mmd).

The data model has been designed to maximise data integrity, however it should be noted that due to the multi-table inhertiance for prompts and responses there is no database-level integrity linking Prompt subclasses and Response subclasses.

## Multi-table inheritance

The data model makes use of [Django multi-table inheritance](https://docs.djangoproject.com/en/5.1/topics/db/models/#multi-table-inheritance) to support multiple prompt types (and associated response types).

This gives the prompt system flexibility, but also adds complexity to the codebase:

- [FeedbackFormAdmin](https://github.com/nationalarchives/ds-feedback/blob/main/app/feedback_forms/admin.py) has additional logic to support rendering and saving prompt subclasses
- [PromptResponseInline](https://github.com/nationalarchives/ds-feedback/blob/main/app/responses/admin.py) has additional logic to render prompt response subclasses and create hyperlinks back to specific prompt types
- [Throughout the API](https://github.com/nationalarchives/ds-feedback/blob/main/app/api/views.py) we need to fetch prompt and prompt response subclasses

## Path pattern matching

While users specify PathPatterns using a wildcard character (e.g. `/about-us/*`), these are stored in the database as a separate `pattern` string and `is_wildcard` boolean, in order to query efficiently.

[FeedbackFormPathPatternDetail](https://github.com/nationalarchives/ds-feedback/blob/main/app/api/views.py) contains the query for matching a URL path against PathPatterns to fetch the correct FeedbackForm.

This query looks for exact (non-wildcard) matches as well as wildcard matches using an inverted `startswith` query. If there is an exact match, it returns the feedback form for that match, otherwise it returns the longest matching pattern.

The performance of this query does not scale well with large numbers of PathPatterns per Project, but we do not expect to reach these volumes. The [pattern-perf-testing branch](https://github.com/nationalarchives/ds-feedback/tree/pattern-perf-testing) contains performance testing and investigation into using a GIN index.

Alternative approaches are welome!

## How to create a new Prompt type

- Create a new [Prompt model](https://github.com/nationalarchives/ds-feedback/blob/main/app/prompts/models.py) subclass
- Create a new [PromptResponse model](https://github.com/nationalarchives/ds-feedback/blob/main/app/responses/models.py) subclass
- Create a new [PromptSerializer](https://github.com/nationalarchives/ds-feedback/blob/main/app/api/serializers.py) subclass
- Create a new [admin area](https://github.com/nationalarchives/ds-feedback/blob/main/app/prompts/admin.py) for the Prompt type
- If the prompt type has foreign key references for choices/options (like RangedPrompt) then:
  - Update [prefetches in the API](https://github.com/nationalarchives/ds-feedback/blob/main/app/api/views.py)
  - Update [PromptResponseSerializer.to_representation()](https://github.com/nationalarchives/ds-feedback/blob/main/app/api/serializers.py) to propagate prefetched values
- Create factories and add prompt specific test cases
- Update the documentation such as [the data model diagram](./data-model.mmd) and [Key Concepts](./key-concepts.md)
- Add an example for the Prompt type to API documentation
