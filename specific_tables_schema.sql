--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9
-- Dumped by pg_dump version 16.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bid_target_audiences; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.bid_target_audiences (
    id integer NOT NULL,
    bid_id integer,
    audience_name character varying(255) NOT NULL,
    ta_category character varying(100),
    broader_category character varying(100),
    exact_ta_definition text,
    mode character varying(50),
    sample_required integer,
    ir numeric(5,2),
    comments text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_best_efforts boolean DEFAULT false
);


ALTER TABLE public.bid_target_audiences OWNER TO neondb_owner;

--
-- Name: bid_target_audiences_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.bid_target_audiences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_target_audiences_id_seq OWNER TO neondb_owner;

--
-- Name: bid_target_audiences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.bid_target_audiences_id_seq OWNED BY public.bid_target_audiences.id;


--
-- Name: bids; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.bids (
    id integer NOT NULL,
    bid_number character varying(50) NOT NULL,
    bid_date date NOT NULL,
    study_name character varying(255) NOT NULL,
    status public.bid_status DEFAULT 'draft'::public.bid_status,
    client integer,
    sales_contact integer,
    vm_contact integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    project_requirement text,
    methodology public.methodology,
    rejection_reason character varying(100),
    rejection_comments text
);


ALTER TABLE public.bids OWNER TO neondb_owner;

--
-- Name: bids_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.bids_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bids_id_seq OWNER TO neondb_owner;

--
-- Name: bids_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.bids_id_seq OWNED BY public.bids.id;


--
-- Name: partners; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.partners (
    id integer NOT NULL,
    partner_id character varying(50) NOT NULL,
    partner_name character varying(255) NOT NULL,
    contact_person character varying(255) NOT NULL,
    contact_email character varying(255) NOT NULL,
    contact_phone character varying(50) DEFAULT 'NA'::character varying,
    company_address text DEFAULT 'NA'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    website character varying(255),
    specialized text[],
    geographic_coverage text[]
);


ALTER TABLE public.partners OWNER TO neondb_owner;

--
-- Name: partners_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.partners_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partners_id_seq OWNER TO neondb_owner;

--
-- Name: partners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.partners_id_seq OWNED BY public.partners.id;


--
-- Name: bid_target_audiences id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_target_audiences ALTER COLUMN id SET DEFAULT nextval('public.bid_target_audiences_id_seq'::regclass);


--
-- Name: bids id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bids ALTER COLUMN id SET DEFAULT nextval('public.bids_id_seq'::regclass);


--
-- Name: partners id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partners ALTER COLUMN id SET DEFAULT nextval('public.partners_id_seq'::regclass);


--
-- Name: bid_target_audiences bid_target_audiences_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_target_audiences
    ADD CONSTRAINT bid_target_audiences_pkey PRIMARY KEY (id);


--
-- Name: bids bids_bid_number_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_bid_number_key UNIQUE (bid_number);


--
-- Name: bids bids_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_pkey PRIMARY KEY (id);


--
-- Name: partners partners_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_email_key UNIQUE (contact_email);


--
-- Name: partners partners_partner_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_partner_id_key UNIQUE (partner_id);


--
-- Name: partners partners_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_pkey PRIMARY KEY (id);


--
-- Name: idx_bid_target_audiences_bid_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_bid_target_audiences_bid_id ON public.bid_target_audiences USING btree (bid_id);


--
-- Name: idx_bids_client; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_bids_client ON public.bids USING btree (client);


--
-- Name: idx_bids_sales_contact; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_bids_sales_contact ON public.bids USING btree (sales_contact);


--
-- Name: idx_bids_vm_contact; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_bids_vm_contact ON public.bids USING btree (vm_contact);


--
-- Name: bid_target_audiences bid_target_audiences_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_target_audiences
    ADD CONSTRAINT bid_target_audiences_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- Name: bids bids_client_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_client_fkey FOREIGN KEY (client) REFERENCES public.clients(id);


--
-- Name: bids bids_sales_contact_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_sales_contact_fkey FOREIGN KEY (sales_contact) REFERENCES public.sales(id);


--
-- PostgreSQL database dump complete
--

