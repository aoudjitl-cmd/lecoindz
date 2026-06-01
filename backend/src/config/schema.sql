-- =============================================
-- COLISGO — Schéma Oracle
-- =============================================

-- Table des utilisateurs
CREATE TABLE CG_USERS (
    id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email       VARCHAR2(255) NOT NULL UNIQUE,
    password    VARCHAR2(255) NOT NULL,
    first_name  VARCHAR2(100) NOT NULL,
    last_name   VARCHAR2(100) NOT NULL,
    phone       VARCHAR2(20),
    avatar_url  VARCHAR2(500),
    is_verified NUMBER(1) DEFAULT 0,
    rating      NUMBER(3,2) DEFAULT 0,
    nb_ratings  NUMBER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des trajets (publiés par les voyageurs)
CREATE TABLE CG_TRIPS (
    id               NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id          NUMBER NOT NULL REFERENCES CG_USERS(id),
    origin_city      VARCHAR2(100) NOT NULL,
    origin_country   VARCHAR2(100) NOT NULL,
    dest_city        VARCHAR2(100) NOT NULL,
    dest_country     VARCHAR2(100) NOT NULL,
    departure_date   DATE NOT NULL,
    arrival_date     DATE NOT NULL,
    max_weight       NUMBER(6,2) NOT NULL,
    max_size         VARCHAR2(20) NOT NULL,
    price_per_kg     NUMBER(8,2) NOT NULL,
    description      VARCHAR2(1000),
    status           VARCHAR2(20) DEFAULT 'ACTIVE',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des annonces de colis
CREATE TABLE CG_PARCELS (
    id             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id        NUMBER NOT NULL REFERENCES CG_USERS(id),
    title          VARCHAR2(255) NOT NULL,
    description    VARCHAR2(1000),
    origin_city    VARCHAR2(100) NOT NULL,
    origin_country VARCHAR2(100) NOT NULL,
    dest_city      VARCHAR2(100) NOT NULL,
    dest_country   VARCHAR2(100) NOT NULL,
    weight         NUMBER(6,2) NOT NULL,
    taille           VARCHAR2(20) NOT NULL,
    deadline_date  DATE,
    photo_url      VARCHAR2(500),
    is_fragile     NUMBER(1) DEFAULT 0,
    status         VARCHAR2(20) DEFAULT 'PENDING',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des réservations
CREATE TABLE CG_BOOKINGS (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parcel_id       NUMBER NOT NULL REFERENCES CG_PARCELS(id),
    trip_id         NUMBER NOT NULL REFERENCES CG_TRIPS(id),
    sender_id       NUMBER NOT NULL REFERENCES CG_USERS(id),
    carrier_id      NUMBER NOT NULL REFERENCES CG_USERS(id),
    agreed_price    NUMBER(8,2) NOT NULL,
    status          VARCHAR2(20) DEFAULT 'PENDING',
    pickup_code     VARCHAR2(10),
    delivery_code   VARCHAR2(10),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des messages
CREATE TABLE CG_MESSAGES (
    id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id  NUMBER NOT NULL REFERENCES CG_BOOKINGS(id),
    sender_id   NUMBER NOT NULL REFERENCES CG_USERS(id),
    content     VARCHAR2(2000) NOT NULL,
    is_read     NUMBER(1) DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des paiements
CREATE TABLE CG_PAYMENTS (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id      NUMBER NOT NULL REFERENCES CG_BOOKINGS(id),
    amount          NUMBER(10,2) NOT NULL,
    commission      NUMBER(10,2) NOT NULL,
    carrier_amount  NUMBER(10,2) NOT NULL,
    status          VARCHAR2(20) DEFAULT 'PENDING',
    payment_ref     VARCHAR2(255),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des avis
CREATE TABLE CG_REVIEWS (
    id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id  NUMBER NOT NULL REFERENCES CG_BOOKINGS(id),
    reviewer_id NUMBER NOT NULL REFERENCES CG_USERS(id),
    reviewed_id NUMBER NOT NULL REFERENCES CG_USERS(id),
    rating      NUMBER(2,1) NOT NULL,
    commentaire     VARCHAR2(1000),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les recherches fréquentes
CREATE INDEX idx_trips_dest    ON CG_TRIPS(dest_city, dest_country, departure_date);
CREATE INDEX idx_parcels_dest  ON CG_PARCELS(dest_city, dest_country, status);
CREATE INDEX idx_bookings_user ON CG_BOOKINGS(sender_id, carrier_id);
CREATE INDEX idx_messages_book ON CG_MESSAGES(booking_id, created_at)