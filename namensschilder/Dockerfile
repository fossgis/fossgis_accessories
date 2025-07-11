FROM ubuntu:24.10
LABEL Name=fossgis-namensschilder Version=0.0.2
RUN apt update 
RUN apt install -y pandoc 
RUN apt install -y texlive 
RUN apt install -y texlive-fonts-extra 
RUN apt install -y texlive-bibtex-extra
RUN apt install -y texlive-latex-base 
RUN apt install -y texlive-latex-extra 
RUN apt install -y texlive-font-utils 
RUN apt install -y texlive-lang-german
RUN apt install -y python3-openpyxl
RUN apt install -y curl locales && \
    apt clean && \  
    rm -rf /var/lib/apt/lists/*

RUN sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=de_DE.UTF-8
ENV LANGUAGE=de_DE.UTF-8 LANG=de_DE.UTF-8 LC_ALL=de_DE.UTF-8
WORKDIR /home/ubuntu
