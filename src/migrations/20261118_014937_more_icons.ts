import { MigrateUpArgs, MigrateDownArgs, sql } from '@payloadcms/db-postgres'

export async function up({ db, payload, req }: MigrateUpArgs): Promise<void> {
  await db.execute(sql`
   ALTER TYPE "public"."enum_pages_blocks_services_items_icon" ADD VALUE 'zap';
  ALTER TYPE "public"."enum_pages_blocks_services_items_icon" ADD VALUE 'trending';
  ALTER TYPE "public"."enum_pages_blocks_services_items_icon" ADD VALUE 'lock';
  ALTER TYPE "public"."enum_pages_blocks_services_items_icon" ADD VALUE 'accessibility';
  ALTER TYPE "public"."enum_pages_blocks_services_items_icon" ADD VALUE 'key';
  ALTER TYPE "public"."enum_pages_blocks_services_items_icon" ADD VALUE 'headset';
  ALTER TYPE "public"."enum__pages_v_blocks_services_items_icon" ADD VALUE 'zap';
  ALTER TYPE "public"."enum__pages_v_blocks_services_items_icon" ADD VALUE 'trending';
  ALTER TYPE "public"."enum__pages_v_blocks_services_items_icon" ADD VALUE 'lock';
  ALTER TYPE "public"."enum__pages_v_blocks_services_items_icon" ADD VALUE 'accessibility';
  ALTER TYPE "public"."enum__pages_v_blocks_services_items_icon" ADD VALUE 'key';
  ALTER TYPE "public"."enum__pages_v_blocks_services_items_icon" ADD VALUE 'headset';`)
}

export async function down({ db, payload, req }: MigrateDownArgs): Promise<void> {
  await db.execute(sql`
   ALTER TABLE "pages_blocks_services_items" ALTER COLUMN "icon" SET DATA TYPE text;
  ALTER TABLE "pages_blocks_services_items" ALTER COLUMN "icon" SET DEFAULT 'code'::text;
  DROP TYPE "public"."enum_pages_blocks_services_items_icon";
  CREATE TYPE "public"."enum_pages_blocks_services_items_icon" AS ENUM('code', 'palette', 'database', 'cart', 'search', 'sparkles', 'shield', 'gauge', 'layout', 'smartphone', 'map', 'bot', 'chart', 'wrench', 'tooth', 'home', 'heart', 'cpu');
  ALTER TABLE "pages_blocks_services_items" ALTER COLUMN "icon" SET DEFAULT 'code'::"public"."enum_pages_blocks_services_items_icon";
  ALTER TABLE "pages_blocks_services_items" ALTER COLUMN "icon" SET DATA TYPE "public"."enum_pages_blocks_services_items_icon" USING "icon"::"public"."enum_pages_blocks_services_items_icon";
  ALTER TABLE "_pages_v_blocks_services_items" ALTER COLUMN "icon" SET DATA TYPE text;
  ALTER TABLE "_pages_v_blocks_services_items" ALTER COLUMN "icon" SET DEFAULT 'code'::text;
  DROP TYPE "public"."enum__pages_v_blocks_services_items_icon";
  CREATE TYPE "public"."enum__pages_v_blocks_services_items_icon" AS ENUM('code', 'palette', 'database', 'cart', 'search', 'sparkles', 'shield', 'gauge', 'layout', 'smartphone', 'map', 'bot', 'chart', 'wrench', 'tooth', 'home', 'heart', 'cpu');
  ALTER TABLE "_pages_v_blocks_services_items" ALTER COLUMN "icon" SET DEFAULT 'code'::"public"."enum__pages_v_blocks_services_items_icon";
  ALTER TABLE "_pages_v_blocks_services_items" ALTER COLUMN "icon" SET DATA TYPE "public"."enum__pages_v_blocks_services_items_icon" USING "icon"::"public"."enum__pages_v_blocks_services_items_icon";`)
}
