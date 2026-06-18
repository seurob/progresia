import { Injectable, OnModuleInit, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { Client as MinioClient } from "minio";

@Injectable()
export class StorageService implements OnModuleInit {
  private readonly logger = new Logger(StorageService.name);
  private readonly client: MinioClient;
  private readonly bucket: string;

  constructor(private readonly config: ConfigService) {
    this.bucket = config.get("MINIO_BUCKET", "progresia-artifacts");
    this.client = new MinioClient({
      endPoint: config.get("MINIO_ENDPOINT", "localhost"),
      port: config.get<number>("MINIO_PORT", 9000),
      useSSL: config.get("MINIO_USE_SSL", "false") === "true",
      accessKey: config.get("MINIO_ACCESS_KEY", "progresia"),
      secretKey: config.get("MINIO_SECRET_KEY", "progresia_secret")
    });
  }

  async onModuleInit() {
    try {
      const exists = await this.client.bucketExists(this.bucket);
      if (!exists) {
        await this.client.makeBucket(this.bucket);
        this.logger.log(`Created MinIO bucket: ${this.bucket}`);
      }
    } catch (err) {
      this.logger.warn(`MinIO bucket init skipped (MinIO may be unavailable): ${err}`);
    }
  }

  async uploadBuffer(objectName: string, buffer: Buffer, contentType: string): Promise<void> {
    await this.client.putObject(this.bucket, objectName, buffer, buffer.length, {
      "Content-Type": contentType
    });
  }

  async getSignedUrl(objectName: string, expirySeconds = 3600): Promise<string> {
    return this.client.presignedGetObject(this.bucket, objectName, expirySeconds);
  }
}
