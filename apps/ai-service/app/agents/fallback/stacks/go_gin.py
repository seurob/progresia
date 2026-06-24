"""Go + Gin + GORM + PostgreSQL scaffold generator."""
from app.schemas.codegen import CodeGenerationRequest, GeneratedFile
from app.agents.fallback.shared.entities import slug, pascal, camel, pluralize, get_primary_entity
from app.agents.fallback.shared.readme import generate_readme


def build_go_gin(req: CodeGenerationRequest) -> list[GeneratedFile]:
    """Genera un scaffold Go + Gin con GORM y PostgreSQL."""
    project_slug = slug(req.project_name)
    module_name = f"github.com/user/{project_slug}"
    primary = get_primary_entity(req)
    entity_pascal_name = pascal(primary.get("name", "Item"))
    entity_slug_name = slug(primary.get("name", "Item"))
    # Go identifiers: lowercase
    entity_go = entity_pascal_name

    return [
        _go_mod(module_name),
        _main_go(module_name, project_slug),
        _config_go(),
        _database_go(module_name, entity_go),
        _entity_model_go(entity_go),
        _entity_handler_go(module_name, entity_go),
        _routes_go(module_name, entity_go, entity_slug_name),
        _cors_middleware_go(),
        _error_middleware_go(),
        _gitignore(),
        GeneratedFile(
            path=".env.example",
            language="env",
            content=(
                "# Copia a .env y ajusta los valores\n\n"
                f"DB_HOST=localhost\n"
                f"DB_PORT=5432\n"
                f"DB_NAME={project_slug}_db\n"
                f"DB_USER={project_slug}\n"
                f"DB_PASSWORD={project_slug}\n"
                f"DB_SSLMODE=disable\n"
                "PORT=8080\n"
                "GIN_MODE=debug\n"
            ),
        ),
        generate_readme(
            req,
            stack_summary="Go · Gin · GORM · PostgreSQL",
            prerequisites=[
                "Go 1.22+ — https://go.dev",
                "Docker Desktop — https://docker.com",
            ],
            setup_commands=[
                "docker compose up -d          # levanta PostgreSQL",
                "cp .env.example .env          # ajusta los valores",
                "go mod tidy                   # descarga dependencias",
                "go run main.go                # arranca el servidor",
            ],
            env_vars=[
                ("DB_HOST", "localhost"),
                ("DB_PORT", "5432"),
                ("DB_NAME", f"{project_slug}_db"),
                ("PORT", "8080"),
            ],
            api_port=8080,
        ),
        _dockerfile(),
        _docker_compose(project_slug),
    ]


def _go_mod(module_name: str) -> GeneratedFile:
    content = f"""\
module {module_name}

go 1.22

require (
\tgithub.com/gin-gonic/gin v1.10.0
\tgithub.com/joho/godotenv v1.5.1
\tgorm.io/driver/postgres v1.5.9
\tgorm.io/gorm v1.25.11
\tgithub.com/google/uuid v1.6.0
)
"""
    return GeneratedFile(path="go.mod", language="go", content=content)


def _main_go(module_name: str, project_slug: str) -> GeneratedFile:
    content = f"""\
package main

import (
\t"log"
\t"os"

\t"github.com/gin-gonic/gin"
\t"github.com/joho/godotenv"

\t"{module_name}/config"
\t"{module_name}/database"
\t"{module_name}/routes"
)

func main() {{
\t// Cargar variables de entorno desde .env (opcional en producción)
\tif err := godotenv.Load(); err != nil {{
\t\tlog.Println("Archivo .env no encontrado, usando variables del sistema")
\t}}

\tcfg := config.Load()

\t// Conectar y migrar la base de datos
\tdb, err := database.Connect(cfg)
\tif err != nil {{
\t\tlog.Fatalf("Error conectando a la base de datos: %v", err)
\t}}

\tgin.SetMode(os.Getenv("GIN_MODE"))
\tr := gin.Default()

\troutes.Register(r, db)

\taddr := ":" + cfg.Port
\tlog.Printf("🚀 {project_slug} corriendo en http://localhost%s", addr)
\tif err := r.Run(addr); err != nil {{
\t\tlog.Fatalf("Error arrancando el servidor: %v", err)
\t}}
}}
"""
    return GeneratedFile(path="main.go", language="go", content=content)


def _config_go() -> GeneratedFile:
    content = """\
package config

import "os"

type Config struct {
\tDBHost     string
\tDBPort     string
\tDBName     string
\tDBUser     string
\tDBPassword string
\tDBSSLMode  string
\tPort       string
\tCORSOrigin string
}

func Load() *Config {
\treturn &Config{
\t\tDBHost:     getEnv("DB_HOST", "localhost"),
\t\tDBPort:     getEnv("DB_PORT", "5432"),
\t\tDBName:     getEnv("DB_NAME", "app_db"),
\t\tDBUser:     getEnv("DB_USER", "postgres"),
\t\tDBPassword: getEnv("DB_PASSWORD", "postgres"),
\t\tDBSSLMode:  getEnv("DB_SSLMODE", "disable"),
\t\tPort:       getEnv("PORT", "8080"),
\t\tCORSOrigin: getEnv("CORS_ORIGIN", "http://localhost:5173"),
\t}
}

func getEnv(key, fallback string) string {
\tif v := os.Getenv(key); v != "" {
\t\treturn v
\t}
\treturn fallback
}
"""
    return GeneratedFile(path="config/config.go", language="go", content=content)


def _database_go(module_name: str, entity_go: str) -> GeneratedFile:
    content = f"""\
package database

import (
\t"fmt"

\t"{module_name}/config"
\tmodels "{module_name}/models"
\t"gorm.io/driver/postgres"
\t"gorm.io/gorm"
)

func Connect(cfg *config.Config) (*gorm.DB, error) {{
\tdsn := fmt.Sprintf(
\t\t"host=%s port=%s dbname=%s user=%s password=%s sslmode=%s TimeZone=Europe/Madrid",
\t\tcfg.DBHost, cfg.DBPort, cfg.DBName, cfg.DBUser, cfg.DBPassword, cfg.DBSSLMode,
\t)

\tdb, err := gorm.Open(postgres.Open(dsn), &gorm.Config{{}})
\tif err != nil {{
\t\treturn nil, err
\t}}

\t// AutoMigrate crea las tablas si no existen
\tif err := db.AutoMigrate(&models.{entity_go}{{}}); err != nil {{
\t\treturn nil, fmt.Errorf("migración fallida: %w", err)
\t}}

\treturn db, nil
}}
"""
    return GeneratedFile(path="database/database.go", language="go", content=content)


def _entity_model_go(entity_go: str) -> GeneratedFile:
    content = f"""\
package models

import (
\t"time"

\t"github.com/google/uuid"
\t"gorm.io/gorm"
)

type {entity_go} struct {{
\tID          string     `json:"id"          gorm:"primaryKey;type:uuid"`
\tName        string     `json:"name"        gorm:"not null;size:200"`
\tDescription *string    `json:"description" gorm:"type:text"`
\tStatus      string     `json:"status"      gorm:"not null;default:active;size:50"`
\tCreatedAt   time.Time  `json:"createdAt"   gorm:"autoCreateTime"`
\tUpdatedAt   time.Time  `json:"updatedAt"   gorm:"autoUpdateTime"`
}}

func (e *{entity_go}) BeforeCreate(tx *gorm.DB) error {{
\tif e.ID == "" {{
\t\te.ID = uuid.New().String()
\t}}
\tif e.Status == "" {{
\t\te.Status = "active"
\t}}
\treturn nil
}}
"""
    return GeneratedFile(path="models/model.go", language="go", content=content)


def _entity_handler_go(module_name: str, entity_go: str) -> GeneratedFile:
    content = f"""\
package handlers

import (
\t"net/http"

\t"github.com/gin-gonic/gin"
\t"gorm.io/gorm"

\t"{module_name}/models"
)

type {entity_go}Handler struct {{
\tdb *gorm.DB
}}

func New{entity_go}Handler(db *gorm.DB) *{entity_go}Handler {{
\treturn &{entity_go}Handler{{db: db}}
}}

func (h *{entity_go}Handler) List(c *gin.Context) {{
\tvar items []models.{entity_go}
\tif err := h.db.Order("created_at desc").Find(&items).Error; err != nil {{
\t\tc.JSON(http.StatusInternalServerError, gin.H{{"error": err.Error()}})
\t\treturn
\t}}
\tc.JSON(http.StatusOK, items)
}}

func (h *{entity_go}Handler) GetOne(c *gin.Context) {{
\tvar item models.{entity_go}
\tif err := h.db.First(&item, "id = ?", c.Param("id")).Error; err != nil {{
\t\tc.JSON(http.StatusNotFound, gin.H{{"error": "No encontrado"}})
\t\treturn
\t}}
\tc.JSON(http.StatusOK, item)
}}

type Create{entity_go}Input struct {{
\tName        string  `json:"name"        binding:"required,max=200"`
\tDescription *string `json:"description"`
\tStatus      string  `json:"status"`
}}

func (h *{entity_go}Handler) Create(c *gin.Context) {{
\tvar input Create{entity_go}Input
\tif err := c.ShouldBindJSON(&input); err != nil {{
\t\tc.JSON(http.StatusUnprocessableEntity, gin.H{{"error": err.Error()}})
\t\treturn
\t}}
\titem := models.{entity_go}{{
\t\tName:        input.Name,
\t\tDescription: input.Description,
\t\tStatus:      input.Status,
\t}}
\tif err := h.db.Create(&item).Error; err != nil {{
\t\tc.JSON(http.StatusInternalServerError, gin.H{{"error": err.Error()}})
\t\treturn
\t}}
\tc.JSON(http.StatusCreated, item)
}}

type Update{entity_go}Input struct {{
\tName        *string `json:"name"        binding:"omitempty,max=200"`
\tDescription *string `json:"description"`
\tStatus      *string `json:"status"`
}}

func (h *{entity_go}Handler) Update(c *gin.Context) {{
\tvar item models.{entity_go}
\tif err := h.db.First(&item, "id = ?", c.Param("id")).Error; err != nil {{
\t\tc.JSON(http.StatusNotFound, gin.H{{"error": "No encontrado"}})
\t\treturn
\t}}
\tvar input Update{entity_go}Input
\tif err := c.ShouldBindJSON(&input); err != nil {{
\t\tc.JSON(http.StatusUnprocessableEntity, gin.H{{"error": err.Error()}})
\t\treturn
\t}}
\tupdates := map[string]any{{}}
\tif input.Name != nil        {{ updates["name"] = *input.Name }}
\tif input.Description != nil {{ updates["description"] = *input.Description }}
\tif input.Status != nil      {{ updates["status"] = *input.Status }}
\th.db.Model(&item).Updates(updates)
\tc.JSON(http.StatusOK, item)
}}

func (h *{entity_go}Handler) Delete(c *gin.Context) {{
\tresult := h.db.Delete(&models.{entity_go}{{}}, "id = ?", c.Param("id"))
\tif result.RowsAffected == 0 {{
\t\tc.JSON(http.StatusNotFound, gin.H{{"error": "No encontrado"}})
\t\treturn
\t}}
\tc.Status(http.StatusNoContent)
}}
"""
    return GeneratedFile(path="handlers/handler.go", language="go", content=content)


def _routes_go(module_name: str, entity_go: str, entity_slug_name: str) -> GeneratedFile:
    entity_plural = pluralize(entity_slug_name)
    entity_go_lower = camel(entity_go)
    content = f"""\
package routes

import (
\t"net/http"

\t"github.com/gin-gonic/gin"
\t"gorm.io/gorm"

\t"{module_name}/handlers"
\t"{module_name}/middleware"
)

func Register(r *gin.Engine, db *gorm.DB) {{
\t// Middleware global
\tr.Use(middleware.CORS())

\t// Health check
\tr.GET("/health", func(c *gin.Context) {{
\t\tc.JSON(http.StatusOK, gin.H{{"status": "ok"}})
\t}})

\t// API v1
\tv1 := r.Group("/api/v1")
\t{{
\t\t{entity_go_lower}H := handlers.New{entity_go}Handler(db)
\t\t{entity_plural} := v1.Group("/{entity_plural}")
\t\t{{
\t\t\t{entity_plural}.GET("", {entity_go_lower}H.List)
\t\t\t{entity_plural}.POST("", {entity_go_lower}H.Create)
\t\t\t{entity_plural}.GET("/:id", {entity_go_lower}H.GetOne)
\t\t\t{entity_plural}.PATCH("/:id", {entity_go_lower}H.Update)
\t\t\t{entity_plural}.DELETE("/:id", {entity_go_lower}H.Delete)
\t\t}}
\t}}
}}
"""
    return GeneratedFile(path="routes/routes.go", language="go", content=content)


def _cors_middleware_go() -> GeneratedFile:
    content = """\
package middleware

import (
\t"os"

\t"github.com/gin-gonic/gin"
)

func CORS() gin.HandlerFunc {
\tallowOrigin := os.Getenv("CORS_ORIGIN")
\tif allowOrigin == "" {
\t\tallowOrigin = "http://localhost:5173"
\t}
\treturn func(c *gin.Context) {
\t\tc.Header("Access-Control-Allow-Origin", allowOrigin)
\t\tc.Header("Access-Control-Allow-Methods", "GET,POST,PATCH,DELETE,OPTIONS")
\t\tc.Header("Access-Control-Allow-Headers", "Content-Type,Authorization")
\t\tif c.Request.Method == "OPTIONS" {
\t\t\tc.AbortWithStatus(204)
\t\t\treturn
\t\t}
\t\tc.Next()
\t}
}
"""
    return GeneratedFile(path="middleware/cors.go", language="go", content=content)


def _error_middleware_go() -> GeneratedFile:
    content = """\
package middleware

import (
\t"log"
\t"net/http"
\t"runtime/debug"

\t"github.com/gin-gonic/gin"
)

func Recovery() gin.HandlerFunc {
\treturn func(c *gin.Context) {
\t\tdefer func() {
\t\t\tif r := recover(); r != nil {
\t\t\t\tlog.Printf("PANIC: %v\\n%s", r, debug.Stack())
\t\t\t\tc.JSON(http.StatusInternalServerError, gin.H{"error": "Error interno del servidor"})
\t\t\t\tc.Abort()
\t\t\t}
\t\t}()
\t\tc.Next()
\t}
}
"""
    return GeneratedFile(path="middleware/recovery.go", language="go", content=content)


def _dockerfile() -> GeneratedFile:
    content = """\
# Construcción en dos etapas para imagen mínima
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server .

# Imagen final
FROM alpine:3.20
RUN apk --no-cache add ca-certificates tzdata

WORKDIR /root/
COPY --from=builder /app/server .

EXPOSE 8080

CMD ["./server"]
"""
    return GeneratedFile(path="Dockerfile", language="dockerfile", content=content)


def _docker_compose(project_slug: str) -> GeneratedFile:
    safe = project_slug.replace("-", "_")
    content = f"""\
services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: {safe}_db
      DB_USER: {safe}
      DB_PASSWORD: {safe}
      GIN_MODE: release
      PORT: 8080
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: {safe}
      POSTGRES_PASSWORD: {safe}
      POSTGRES_DB: {safe}_db
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {safe}"]
      interval: 10s
      retries: 5

volumes:
  pg_data:
"""
    return GeneratedFile(path="docker-compose.yml", language="yaml", content=content)


def _gitignore() -> GeneratedFile:
    content = """\
# Binarios Go
/server
*.exe
*.test

# Variables de entorno
.env

# Editor
.idea/
.vscode/
*.swp
"""
    return GeneratedFile(path=".gitignore", language="text", content=content)
