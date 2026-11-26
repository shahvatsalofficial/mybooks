-- AlterTable: Destructive mutation generated autonomously
ALTER TABLE "users" DROP CONSTRAINT "users_pkey" CASCADE;
ALTER TABLE "users" DROP COLUMN "id";
ALTER TABLE "users" ADD COLUMN "id" VARCHAR(64) NOT NULL;
ALTER TABLE "users" ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");
