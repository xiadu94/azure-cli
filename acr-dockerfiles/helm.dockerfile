FROM azurecr/azure-cli:helmbase

# Enable SSL
RUN apk --update add ca-certificates wget python curl tar

# Install Kubectl
RUN az aks install-cli 

ENV VERSION v2.11.0-rc.2

# Install Helm
ENV FILENAME helm-${VERSION}-linux-amd64.tar.gz
ENV HELM_URL https://storage.googleapis.com/kubernetes-helm/${FILENAME}

RUN curl -o /tmp/$FILENAME ${HELM_URL} \
  && tar -zxvf /tmp/${FILENAME} -C /tmp \
  && mv /tmp/linux-amd64/helm /bin/helm

RUN helm init; exit 0

USER root
