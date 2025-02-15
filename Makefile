NEXTJS_DIR=frontend
FASTAPI_DIR=backend
LAMBDA_DIR=backend/sam

NEXTJS_PORT=3000
FASTAPI_PORT=8000
LAMBDA_PORT=9000

.PHONY: run-frontend run-backend run-lambda

run-frontend:
	cd $(NEXTJS_DIR) && npm run dev &

run-backend:
	cd $(FASTAPI_DIR) && uvicorn main:app --port $(FASTAPI_PORT) --reload &

run-sam:
	cd $(LAMBDA_DIR) && sam local start-api --port $(LAMBDA_PORT) &

build-sam:
	cp requirements.txt backend/lambda && cd $(LAMBDA_DIR) && sam build --template-file template.yaml --use-container --no-cached && rm ../lambda/requirements.txt

start-background: run-frontend run-backend run-lambda
	@echo "All services started in background"

stop:
	@echo "Stopping all services..."
	@pkill -f "npm run dev"
	@pkill -f "uvicorn main:app"
	@pkill -f "sam local start-api"
	@echo "All services successfully stopped"
