-- AlterTable
ALTER TABLE "Tenant" ADD COLUMN     "metadataRetentionEnabled" BOOLEAN NOT NULL DEFAULT false;

-- AlterTable
ALTER TABLE "Camera" ADD COLUMN     "evidenceMode" VARCHAR(10) NOT NULL DEFAULT 'skeleton',
ADD COLUMN     "snapshotAuthorizedAt" TIMESTAMPTZ(3);

-- AlterTable
ALTER TABLE "Incident" ADD COLUMN     "evidenceMode" VARCHAR(10) NOT NULL DEFAULT 'skeleton',
ADD COLUMN     "poseRedactedAt" TIMESTAMPTZ(3);

-- AlterTable
ALTER TABLE "EventReceipt" ADD COLUMN     "redactedAt" TIMESTAMPTZ(3);

-- CreateTable
CREATE TABLE "Evidence" (
    "id" UUID NOT NULL,
    "tenantId" UUID NOT NULL,
    "incidentId" UUID NOT NULL,
    "eventId" UUID NOT NULL,
    "state" VARCHAR(16) NOT NULL DEFAULT 'AWAITING',
    "inputHash" CHAR(64),
    "storedHash" CHAR(64),
    "objectKey" VARCHAR(50),
    "bytes" INTEGER NOT NULL DEFAULT 0,
    "receivedAt" TIMESTAMPTZ(3),
    "expiresAt" TIMESTAMPTZ(3) NOT NULL,
    "deletedAt" TIMESTAMPTZ(3),

    CONSTRAINT "Evidence_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Evidence_incidentId_key" ON "Evidence"("incidentId");

-- CreateIndex
CREATE UNIQUE INDEX "Evidence_objectKey_key" ON "Evidence"("objectKey");

-- CreateIndex
CREATE INDEX "Evidence_state_expiresAt_idx" ON "Evidence"("state", "expiresAt");

-- CreateIndex
CREATE UNIQUE INDEX "Evidence_tenantId_id_key" ON "Evidence"("tenantId", "id");

-- CreateIndex
CREATE UNIQUE INDEX "Evidence_tenantId_incidentId_key" ON "Evidence"("tenantId", "incidentId");

-- AddForeignKey
ALTER TABLE "Evidence" ADD CONSTRAINT "Evidence_tenantId_incidentId_fkey" FOREIGN KEY ("tenantId", "incidentId") REFERENCES "Incident"("tenantId", "id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- Closed application states and bounded storage remain database invariants.
ALTER TABLE "Camera" ADD CONSTRAINT "Camera_evidenceMode_check" CHECK ("evidenceMode" IN ('none','skeleton','snapshot'));
ALTER TABLE "Incident" ADD CONSTRAINT "Incident_evidenceMode_check" CHECK ("evidenceMode" IN ('none','skeleton','snapshot'));
ALTER TABLE "Evidence" ADD CONSTRAINT "Evidence_state_check" CHECK ("state" IN ('AWAITING','AVAILABLE','DELETED','EXPIRED'));
ALTER TABLE "Evidence" ADD CONSTRAINT "Evidence_bytes_check" CHECK ("bytes" BETWEEN 0 AND 2097152);
