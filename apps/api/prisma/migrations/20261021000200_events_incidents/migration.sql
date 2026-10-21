-- CreateEnum
CREATE TYPE "SourceMode" AS ENUM ('SIMULATED', 'REPLAY', 'LIVE');

-- CreateEnum
CREATE TYPE "DetectionKind" AS ENUM ('PERSON_ON_FLOOR', 'POSSIBLE_FALL');

-- CreateEnum
CREATE TYPE "DeliveryClass" AS ENUM ('TEST', 'CURRENT', 'DELAYED', 'CLOCK_UNCERTAIN');

-- CreateEnum
CREATE TYPE "IncidentStatus" AS ENUM ('OPEN', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED', 'DISMISSED');

-- CreateEnum
CREATE TYPE "IncidentReview" AS ENUM ('UNREVIEWED', 'PERSON_ON_FLOOR_CONFIRMED', 'FALL_REPORTED', 'FALSE_POSITIVE', 'INCONCLUSIVE');

-- CreateEnum
CREATE TYPE "IncidentOutcome" AS ENUM ('ASSISTANCE_RECORDED', 'NO_ASSISTANCE_NEEDED', 'INCONCLUSIVE', 'TEST_COMPLETED');

-- CreateEnum
CREATE TYPE "DismissReason" AS ENUM ('FALSE_DETECTION', 'TEST_EVENT', 'DUPLICATE', 'OTHER');

-- CreateEnum
CREATE TYPE "IntentStatus" AS ENUM ('PENDING', 'DELIVERED');

-- CreateEnum
CREATE TYPE "NotificationChannel" AS ENUM ('SIMULATED');

-- AlterTable
ALTER TABLE "Camera" ADD COLUMN     "activeRunId" UUID,
ADD COLUMN     "heartbeatReceivedAt" TIMESTAMPTZ(3),
ADD COLUMN     "heartbeatSequence" BIGINT,
ADD COLUMN     "lastHeartbeat" JSONB;

-- AlterTable
ALTER TABLE "AuditEntry" ADD COLUMN     "fromVersion" INTEGER,
ADD COLUMN     "incidentActionId" UUID,
ADD COLUMN     "incidentId" UUID,
ADD COLUMN     "resultCode" VARCHAR(60),
ADD COLUMN     "toVersion" INTEGER;

-- CreateTable
CREATE TABLE "CameraRun" (
    "tenantId" UUID NOT NULL,
    "cameraId" UUID NOT NULL,
    "runId" UUID NOT NULL,
    "firstReceivedAt" TIMESTAMPTZ(3) NOT NULL,
    "retiredAt" TIMESTAMPTZ(3),

    CONSTRAINT "CameraRun_pkey" PRIMARY KEY ("tenantId","cameraId","runId")
);

-- CreateTable
CREATE TABLE "Incident" (
    "id" UUID NOT NULL,
    "tenantId" UUID NOT NULL,
    "siteId" UUID NOT NULL,
    "cameraId" UUID NOT NULL,
    "episodeId" UUID NOT NULL,
    "originEventId" UUID NOT NULL,
    "runId" UUID NOT NULL,
    "episodeHash" CHAR(64) NOT NULL,
    "kind" "DetectionKind" NOT NULL,
    "mode" "SourceMode" NOT NULL,
    "deliveryClass" "DeliveryClass" NOT NULL,
    "status" "IncidentStatus" NOT NULL DEFAULT 'OPEN',
    "review" "IncidentReview" NOT NULL DEFAULT 'UNREVIEWED',
    "outcome" "IncidentOutcome",
    "dismissReason" "DismissReason",
    "version" INTEGER NOT NULL DEFAULT 1,
    "occurredAt" TIMESTAMPTZ(3) NOT NULL,
    "detectedAt" TIMESTAMPTZ(3) NOT NULL,
    "receivedAt" TIMESTAMPTZ(3) NOT NULL,
    "sourceOffsetMs" BIGINT,
    "signals" JSONB,
    "pose" JSONB,
    "versions" JSONB,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "Incident_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventReceipt" (
    "id" UUID NOT NULL,
    "tenantId" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "eventId" UUID NOT NULL,
    "episodeId" UUID NOT NULL,
    "payloadHash" CHAR(64) NOT NULL,
    "payload" JSONB,
    "receivedAt" TIMESTAMPTZ(3) NOT NULL,
    "deliveryClass" "DeliveryClass" NOT NULL,
    "incidentId" UUID,
    "expiredAt" TIMESTAMPTZ(3),

    CONSTRAINT "EventReceipt_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "IncidentAction" (
    "id" UUID NOT NULL,
    "tenantId" UUID NOT NULL,
    "incidentId" UUID NOT NULL,
    "actorId" UUID NOT NULL,
    "actionId" UUID NOT NULL,
    "action" VARCHAR(30) NOT NULL,
    "payloadHash" CHAR(64) NOT NULL,
    "payload" JSONB,
    "result" JSONB NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "IncidentAction_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "NotificationIntent" (
    "id" UUID NOT NULL,
    "tenantId" UUID NOT NULL,
    "incidentId" UUID NOT NULL,
    "key" VARCHAR(100) NOT NULL,
    "status" "IntentStatus" NOT NULL DEFAULT 'PENDING',
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "nextAttemptAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "lastErrorCode" VARCHAR(60),
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "NotificationIntent_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "NotificationDelivery" (
    "id" UUID NOT NULL,
    "tenantId" UUID NOT NULL,
    "intentId" UUID NOT NULL,
    "channel" "NotificationChannel" NOT NULL DEFAULT 'SIMULATED',
    "message" VARCHAR(300) NOT NULL,
    "urgent" BOOLEAN NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "NotificationDelivery_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "Incident_tenantId_siteId_occurredAt_id_idx" ON "Incident"("tenantId", "siteId", "occurredAt", "id");

-- CreateIndex
CREATE INDEX "Incident_tenantId_status_createdAt_id_idx" ON "Incident"("tenantId", "status", "createdAt", "id");

-- CreateIndex
CREATE INDEX "Incident_tenantId_createdAt_id_idx" ON "Incident"("tenantId", "createdAt", "id");

-- CreateIndex
CREATE UNIQUE INDEX "Incident_tenantId_id_key" ON "Incident"("tenantId", "id");

-- CreateIndex
CREATE UNIQUE INDEX "Incident_cameraId_episodeId_key" ON "Incident"("cameraId", "episodeId");

-- CreateIndex
CREATE INDEX "EventReceipt_tenantId_incidentId_idx" ON "EventReceipt"("tenantId", "incidentId");

-- CreateIndex
CREATE UNIQUE INDEX "EventReceipt_deviceId_eventId_key" ON "EventReceipt"("deviceId", "eventId");

-- CreateIndex
CREATE INDEX "IncidentAction_tenantId_incidentId_createdAt_id_idx" ON "IncidentAction"("tenantId", "incidentId", "createdAt", "id");

-- CreateIndex
CREATE UNIQUE INDEX "IncidentAction_tenantId_id_key" ON "IncidentAction"("tenantId", "id");

-- CreateIndex
CREATE UNIQUE INDEX "IncidentAction_tenantId_actionId_key" ON "IncidentAction"("tenantId", "actionId");

-- CreateIndex
CREATE UNIQUE INDEX "NotificationIntent_incidentId_key" ON "NotificationIntent"("incidentId");

-- CreateIndex
CREATE UNIQUE INDEX "NotificationIntent_key_key" ON "NotificationIntent"("key");

-- CreateIndex
CREATE INDEX "NotificationIntent_status_nextAttemptAt_createdAt_id_idx" ON "NotificationIntent"("status", "nextAttemptAt", "createdAt", "id");

-- CreateIndex
CREATE UNIQUE INDEX "NotificationIntent_tenantId_id_key" ON "NotificationIntent"("tenantId", "id");

-- CreateIndex
CREATE UNIQUE INDEX "NotificationIntent_tenantId_incidentId_key" ON "NotificationIntent"("tenantId", "incidentId");

-- CreateIndex
CREATE UNIQUE INDEX "NotificationDelivery_intentId_key" ON "NotificationDelivery"("intentId");

-- CreateIndex
CREATE INDEX "NotificationDelivery_tenantId_createdAt_id_idx" ON "NotificationDelivery"("tenantId", "createdAt", "id");

-- CreateIndex
CREATE UNIQUE INDEX "NotificationDelivery_tenantId_intentId_key" ON "NotificationDelivery"("tenantId", "intentId");

-- CreateIndex
CREATE INDEX "AuditEntry_tenantId_incidentId_createdAt_id_idx" ON "AuditEntry"("tenantId", "incidentId", "createdAt", "id");

-- AddForeignKey
ALTER TABLE "AuditEntry" ADD CONSTRAINT "AuditEntry_tenantId_incidentId_fkey" FOREIGN KEY ("tenantId", "incidentId") REFERENCES "Incident"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditEntry" ADD CONSTRAINT "AuditEntry_tenantId_incidentActionId_fkey" FOREIGN KEY ("tenantId", "incidentActionId") REFERENCES "IncidentAction"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CameraRun" ADD CONSTRAINT "CameraRun_tenantId_cameraId_fkey" FOREIGN KEY ("tenantId", "cameraId") REFERENCES "Camera"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Incident" ADD CONSTRAINT "Incident_tenantId_siteId_fkey" FOREIGN KEY ("tenantId", "siteId") REFERENCES "Site"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Incident" ADD CONSTRAINT "Incident_tenantId_cameraId_fkey" FOREIGN KEY ("tenantId", "cameraId") REFERENCES "Camera"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventReceipt" ADD CONSTRAINT "EventReceipt_tenantId_deviceId_fkey" FOREIGN KEY ("tenantId", "deviceId") REFERENCES "Device"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventReceipt" ADD CONSTRAINT "EventReceipt_tenantId_incidentId_fkey" FOREIGN KEY ("tenantId", "incidentId") REFERENCES "Incident"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "IncidentAction" ADD CONSTRAINT "IncidentAction_tenantId_incidentId_fkey" FOREIGN KEY ("tenantId", "incidentId") REFERENCES "Incident"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "IncidentAction" ADD CONSTRAINT "IncidentAction_tenantId_actorId_fkey" FOREIGN KEY ("tenantId", "actorId") REFERENCES "User"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "NotificationIntent" ADD CONSTRAINT "NotificationIntent_tenantId_incidentId_fkey" FOREIGN KEY ("tenantId", "incidentId") REFERENCES "Incident"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "NotificationDelivery" ADD CONSTRAINT "NotificationDelivery_tenantId_intentId_fkey" FOREIGN KEY ("tenantId", "intentId") REFERENCES "NotificationIntent"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;
