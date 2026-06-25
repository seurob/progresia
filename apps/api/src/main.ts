import "./instrument";
import { ValidationPipe } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { HttpAdapterHost, NestFactory } from "@nestjs/core";
import { DocumentBuilder, SwaggerModule } from "@nestjs/swagger";
import { SentryExceptionFilter } from "./common/filters/sentry-exception.filter";
import { AppModule } from "./modules/app.module";

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const configService = app.get(ConfigService);
  const port = configService.get<number>("API_PORT", 3000);

  const allowedOrigins = configService
    .get<string>("CORS_ORIGINS", "http://localhost:5173")
    .split(",")
    .map((o) => o.trim());

  app.setGlobalPrefix("api");
  app.enableCors({
    origin: allowedOrigins,
    methods: ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
    credentials: true
  });
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true
    })
  );
  app.useGlobalFilters(new SentryExceptionFilter(app.get(HttpAdapterHost)));

  const openApiConfig = new DocumentBuilder()
    .setTitle("ProgresIA Studio API")
    .setDescription("API principal de ProgresIA Studio.")
    .setVersion("0.1.0")
    .addBearerAuth()
    .build();

  const document = SwaggerModule.createDocument(app, openApiConfig);
  SwaggerModule.setup("api/docs", app, document);

  await app.listen(port);
}

void bootstrap();
