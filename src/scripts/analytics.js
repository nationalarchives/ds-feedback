import {
  GA4,
  helpers,
} from "@nationalarchives/frontend/nationalarchives/analytics.mjs";

const ga4Id = document.documentElement.getAttribute("data-ga4id");
if (ga4Id) {
  const analytics = new GA4({ id: ga4Id });

  analytics.addListeners(document.documentElement, "document", [
    {
      eventName: "double_click",
      on: "dblclick",
      data: {
        // eslint-disable-next-line no-unused-vars
        state: ($el, $scope, event, index) => helpers.getXPathTo(event.target),
        // eslint-disable-next-line no-unused-vars
        value: ($el, $scope, event, index) => event.target.innerHTML,
      },
    },
  ]);
}
