import {
  Cookies,
  initAll,
} from "@nationalarchives/frontend/nationalarchives/all.mjs";

const cookiesDomain =
  document.documentElement.getAttribute("data-cookiesdomain");
if (cookiesDomain) {
  new Cookies({ domain: cookiesDomain });
}

initAll();
