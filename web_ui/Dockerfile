# syntax=docker/dockerfile:1.7

#############
# build_rest_api_specs
#############

FROM node_image as build_rest_api_specs

ARG LOCATION=/home/app/rest-api-specs/

WORKDIR ${LOCATION}

COPY --link ./package.json .
COPY --link --from=docs_context rest_api /home/app/docs/rest_api/
COPY --link --from=api_context schemas /home/app/interactive_ai/services/api/schemas/

RUN npm run build:rest-openapi-spec


#############
# web_ui_deps
#############
FROM node_image AS web_ui_deps

ARG LOCATION=/home/app/web_ui/

WORKDIR ${LOCATION}

COPY --link package.json ./
COPY --link package-lock.json ./
RUN npm ci --audit=false

COPY --link ./eslint.config.mjs ./
COPY --link ./.prettierrc ./
COPY --link ./tsconfig.json ./
COPY --link ./rsbuild.config.ts ./
COPY --link ./dev-proxy.ts ./

COPY --link src/ src/
COPY --link public/ public/

COPY --from=docs_context rest_api /home/app/docs/rest_api/
COPY --from=api_context schemas /home/app/interactive_ai/services/api/schemas/

RUN REACT_APP_BUILD_TARGET=app npm run-script build && mv build main-app
RUN REACT_APP_BUILD_TARGET=admin REACT_APP_PUBLIC_PATH=/intel-admin/ npm run-script build && mv build admin-app

#######
# web_ui
#######

FROM nginx_image AS web_ui

COPY --link --from=web_ui_deps /home/app/web_ui/main-app/ /usr/share/nginx/webui/
COPY --link --from=web_ui_deps /home/app/web_ui/admin-app/ /usr/share/nginx/admin-app/
RUN useradd -u 10001 webservice
COPY --link nginx.conf /etc/nginx/nginx.conf
COPY --link src/maintenance /maintenance
COPY --link --from=build_rest_api_specs /home/app/rest-api-specs/public/openapi-spec.json /usr/share/nginx/webui/openapi-spec.json

USER webservice
EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
