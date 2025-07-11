# how to ? !

hannes und janine 🤝 axel
- 2023 [fossgis_accessories/namensschilder at master · fossgis/fossgis_accessories (github.com)](https://github.com/fossgis/fossgis_accessories/tree/master/namensschilder) 
- 2024 [fossgis_accessories/namensschilder at master · axza/fossgis_accessories (github.com)](https://github.com/axza/fossgis_accessories/tree/master/namensschilder) 
- 2025 [(https://tja.mal.schaun.was.weird)???](https://tja.mal.schaun.was.weird)

## build image
```
docker build --pull --rm -f "Dockerfile" -t  "."
```

### run image (interactive -it)
```
docker run --rm -it  namensschilder:latest
docker run -v $(pwd):/app -it --rm namensschilder:latest
```



## docker compose
```
docker compose up -d
```

### attach to terminal in container:
```
docker exec -it namensschilder bash
```