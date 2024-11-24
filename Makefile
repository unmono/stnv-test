containers:
	docker image rm starnavi
	docker build -t starnavi .
	docker run --rm -p 8000:8000 starnavi