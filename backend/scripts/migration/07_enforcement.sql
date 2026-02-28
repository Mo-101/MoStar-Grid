-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 7: ENFORCEMENT (Idempotent Foreign Keys)
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. SOUL LAYER FKs
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_ifa_rules_odu') THEN
        ALTER TABLE soul.ifa_rules ADD CONSTRAINT fk_ifa_rules_odu FOREIGN KEY (odu_number) REFERENCES soul.ifa_odu(odu_number) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_entity_cap') THEN
        ALTER TABLE soul.entity_capabilities ADD CONSTRAINT fk_entity_cap FOREIGN KEY (entity_id) REFERENCES soul.entities(entity_id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_entity_vow') THEN
        ALTER TABLE soul.entity_vows ADD CONSTRAINT fk_entity_vow FOREIGN KEY (entity_id) REFERENCES soul.entities(entity_id) ON DELETE CASCADE;
    END IF;
END $$;

-- 2. MIND LAYER FKs
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_framework_component') THEN
        ALTER TABLE mind.decision_frameworks ADD CONSTRAINT fk_framework_component FOREIGN KEY (component_id) REFERENCES mind.ai_components(component_id) ON DELETE CASCADE;
    END IF;
END $$;

-- 3. BODY LAYER FKs
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_endpoint_owner') THEN
        ALTER TABLE body.api_endpoints ADD CONSTRAINT fk_endpoint_owner FOREIGN KEY (entity_owner) REFERENCES soul.entities(entity_id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_module_owner') THEN
        ALTER TABLE body.executable_modules ADD CONSTRAINT fk_module_owner FOREIGN KEY (owner_entity) REFERENCES soul.entities(entity_id) ON DELETE CASCADE;
    END IF;
END $$;

-- 4. CONSCIOUSNESS LAYER FKs
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_mom_source') THEN
        ALTER TABLE consciousness.moment_relationships ADD CONSTRAINT fk_mom_source FOREIGN KEY (source_id) REFERENCES consciousness.moments(moment_id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_mom_target') THEN
        ALTER TABLE consciousness.moment_relationships ADD CONSTRAINT fk_mom_target FOREIGN KEY (target_id) REFERENCES consciousness.moments(moment_id) ON DELETE CASCADE;
    END IF;
END $$;

-- 5. ENRICHMENT LAYER FKs
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_odu_enrich') THEN
        ALTER TABLE soul.ifa_odu_enrichment ADD CONSTRAINT fk_odu_enrich FOREIGN KEY (odu_number) REFERENCES soul.ifa_odu(odu_number) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_word_enrich') THEN
        ALTER TABLE soul.ibibio_word_enrichment ADD CONSTRAINT fk_word_enrich FOREIGN KEY (word) REFERENCES soul.ibibio_words(word) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_map_word') THEN
        ALTER TABLE soul.word_audio_map ADD CONSTRAINT fk_map_word FOREIGN KEY (word) REFERENCES soul.ibibio_words(word) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_map_audio') THEN
        ALTER TABLE soul.word_audio_map ADD CONSTRAINT fk_map_audio FOREIGN KEY (audio_id) REFERENCES soul.audio_samples(audio_id) ON DELETE CASCADE;
    END IF;
END $$;
