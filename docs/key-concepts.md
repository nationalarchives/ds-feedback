# Key Concepts

## Prompts

A prompt is a question to be asked to a user, there are currently the following types of prompt:

- TextPrompt - A question with a free text answer
- BinaryPrompt - A question with two options (commonly yes/no)
- RangedPrompt - A multiple choice question, only a single answer can be picked

## Feedback forms

Each feedback form is a series of prompts, which are asked one at a time. Users are not required to answer all prompts. There is a maximum of 3 prompts per feedback form, in order to keep the feedback quick and unobtrusive. Only one feedback form will be displayed on a page.

### Path patterns

Each feedback form has a number of path patterns which are used to determine whether the form is displayed on a specific URL.
Each path pattern is a URL path (for example `/explore-the-collection/explore-by-topic/`) which allows the feedback form to be displayed on that URL.

Path patterns can also include wildcards (`*`) which allow them to match any subsequent URL. For example the path pattern `/explore-the-collection/*` would allow the feedback form to be displayed on the URL path `/explore-the-collection/stories/`.

For any page, the feedback form which most specifically matches the URL path will be chosen. This allows generic feedback forms to be used for most pages, while allowing specific feedback forms to be used on certain pages.

## Projects

Each project is a collection of feedback forms, designed to be used on a site (for example [https://beta.nationalarchives.gov.uk/](https://beta.nationalarchives.gov.uk/)). API access is granted per project.

## Responses

A response represents the feedback from a user for a feedback form. Each response contains the URL the user was on, any custom metadata sent to the API (for example this could be browser statistics or an analytics tracking token), and any prompt responses.

## Prompt responses

Each prompt response is a response from a user to a prompt.

## API

The API is split into 3 components:

### Submit

The Submit API is designed to be used by a web server submit user feedback.
This API requires the "Submit Responses" role.

### Explore

The Explore API is designed to be used by users or services to explore or export user feedback.
This API requires the "Explore Responses" role.

### Core

The Core API includes routes which are common across different use cases.
This API requries either the "Submit Responses" or "Explore Responses" role.
