-- Extension for UUIDs if needed, though Serial/Integer is fine for this scale
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS examens CASCADE;
DROP TABLE IF EXISTS inscriptions CASCADE;
DROP TABLE IF EXISTS modules CASCADE;
DROP TABLE IF EXISTS etudiants CASCADE;
DROP TABLE IF EXISTS formations CASCADE;
DROP TABLE IF EXISTS professeurs CASCADE;
DROP TABLE IF EXISTS lieux_examen CASCADE;
DROP TABLE IF EXISTS departements CASCADE;

-- 1. Départements
CREATE TABLE departements (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Formations (Ex: Licence Informatique, Master IA...)
CREATE TABLE formations (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    dept_id INTEGER REFERENCES departements(id) ON DELETE CASCADE,
    nb_modules INTEGER DEFAULT 6
);

-- 3. Professeurs
CREATE TABLE professeurs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    dept_id INTEGER REFERENCES departements(id) ON DELETE SET NULL,
    email VARCHAR(150),
    specialite VARCHAR(100)
);

-- 4. Etudiants
CREATE TABLE etudiants (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    formation_id INTEGER REFERENCES formations(id) ON DELETE CASCADE,
    promo VARCHAR(20) -- Ex: 'L3', 'M1'
);

-- 5. Modules (Matières)
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    credits INTEGER DEFAULT 3,
    formation_id INTEGER REFERENCES formations(id) ON DELETE CASCADE,
    semestre INTEGER CHECK (semestre > 0 AND semestre <= 6)
);

-- 6. Lieux d'examen (Salles, Amphis)
CREATE TABLE lieux_examen (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE, -- Ex: 'Amphi A', 'Salle 12'
    capacite INTEGER NOT NULL CHECK (capacite > 0),
    type VARCHAR(20) CHECK (type IN ('Amphi', 'Salle', 'Laboratoire')),
    batiment VARCHAR(50)
);

-- 7. Inscriptions (Lien Etudiant - Module)
CREATE TABLE inscriptions (
    etudiant_id INTEGER REFERENCES etudiants(id) ON DELETE CASCADE,
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    note NUMERIC(4, 2), -- Note optionnelle pour historique
    PRIMARY KEY (etudiant_id, module_id)
);

-- 8. Examens (Le planning généré)
CREATE TABLE examens (
    id SERIAL PRIMARY KEY,
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    prof_surveillant_id INTEGER REFERENCES professeurs(id), -- Surveillant principal
    salle_id INTEGER REFERENCES lieux_examen(id),
    date_examen DATE NOT NULL,
    creneau_debut TIME NOT NULL, -- Ex: 08:30
    creneau_fin TIME NOT NULL,   -- Ex: 10:00
    CONSTRAINT check_duree CHECK (creneau_fin > creneau_debut)
);

-- Index pour optimiser les recherches de conflits
CREATE INDEX idx_examens_date_creneau ON examens(date_examen, creneau_debut, creneau_fin);
CREATE INDEX idx_inscriptions_module ON inscriptions(module_id);
CREATE INDEX idx_etudiants_formation ON etudiants(formation_id);
