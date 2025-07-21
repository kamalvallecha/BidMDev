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

--
-- Name: bid_status; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.bid_status AS ENUM (
    'draft',
    'submitted',
    'infield',
    'closure',
    'ready_for_invoice',
    'invoiced'
);


ALTER TYPE public.bid_status OWNER TO neondb_owner;

--
-- Name: methodology; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.methodology AS ENUM (
    'quant',
    'qual',
    'both'
);


ALTER TYPE public.methodology OWNER TO neondb_owner;

--
-- Name: region; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.region AS ENUM (
    'north',
    'south',
    'east',
    'west'
);


ALTER TYPE public.region OWNER TO neondb_owner;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bid_audience_countries; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.bid_audience_countries (
    id integer NOT NULL,
    bid_id integer,
    audience_id integer,
    country character varying(100) NOT NULL,
    sample_size integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_best_efforts boolean DEFAULT false
);


ALTER TABLE public.bid_audience_countries OWNER TO neondb_owner;

--
-- Name: bid_audience_countries_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.bid_audience_countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_audience_countries_id_seq OWNER TO neondb_owner;

--
-- Name: bid_audience_countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.bid_audience_countries_id_seq OWNED BY public.bid_audience_countries.id;


--
-- Name: bid_partners; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.bid_partners (
    id integer NOT NULL,
    bid_id integer,
    partner_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.bid_partners OWNER TO neondb_owner;

--
-- Name: bid_partners_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.bid_partners_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_partners_id_seq OWNER TO neondb_owner;

--
-- Name: bid_partners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.bid_partners_id_seq OWNED BY public.bid_partners.id;


--
-- Name: bid_po_numbers; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.bid_po_numbers (
    id integer NOT NULL,
    bid_id integer,
    po_number character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.bid_po_numbers OWNER TO neondb_owner;

--
-- Name: bid_po_numbers_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.bid_po_numbers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_po_numbers_id_seq OWNER TO neondb_owner;

--
-- Name: bid_po_numbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.bid_po_numbers_id_seq OWNED BY public.bid_po_numbers.id;


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
-- Name: clients; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.clients (
    id integer NOT NULL,
    client_id character varying(50) NOT NULL,
    client_name character varying(255) NOT NULL,
    contact_person character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(50) NOT NULL,
    country character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.clients OWNER TO neondb_owner;

--
-- Name: clients_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.clients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clients_id_seq OWNER TO neondb_owner;

--
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- Name: partner_audience_responses; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.partner_audience_responses (
    id integer NOT NULL,
    partner_response_id integer,
    bid_id integer,
    audience_id integer,
    country character varying(100) NOT NULL,
    allocation integer DEFAULT 0 NOT NULL,
    n_delivered integer DEFAULT 0,
    quality_rejects integer DEFAULT 0,
    final_loi numeric(5,2),
    final_ir numeric(5,2),
    final_timeline integer,
    final_cpi numeric(10,2),
    cpi numeric(10,2),
    communication character varying(255),
    engagement character varying(255),
    problem_solving character varying(255),
    additional_feedback text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    field_close_date date,
    commitment integer DEFAULT 0,
    timeline_days integer DEFAULT 0,
    comments text DEFAULT ''::text,
    initial_cost numeric(10,2) DEFAULT 0,
    final_cost numeric(10,2) DEFAULT 0,
    savings numeric(10,2) DEFAULT 0,
    communication_rating integer,
    engagement_rating integer,
    problem_solving_rating integer,
    is_best_efforts boolean DEFAULT false,
    commitment_type character varying(10) DEFAULT 'fixed'::character varying,
    CONSTRAINT check_commitment_type CHECK (((commitment_type)::text = ANY ((ARRAY['fixed'::character varying, 'be_max'::character varying])::text[])))
);


ALTER TABLE public.partner_audience_responses OWNER TO neondb_owner;

--
-- Name: partner_audience_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.partner_audience_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_audience_responses_id_seq OWNER TO neondb_owner;

--
-- Name: partner_audience_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.partner_audience_responses_id_seq OWNED BY public.partner_audience_responses.id;


--
-- Name: partner_links; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.partner_links (
    id integer NOT NULL,
    bid_id integer,
    partner_id integer,
    token character varying(255) NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    notification_sent boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.partner_links OWNER TO neondb_owner;

--
-- Name: partner_links_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.partner_links_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_links_id_seq OWNER TO neondb_owner;

--
-- Name: partner_links_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.partner_links_id_seq OWNED BY public.partner_links.id;


--
-- Name: partner_responses; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.partner_responses (
    id integer NOT NULL,
    bid_id integer,
    partner_id integer,
    loi integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying,
    currency character varying(3) DEFAULT 'USD'::character varying,
    response_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    pmf integer DEFAULT 0,
    timeline integer DEFAULT 0,
    invoice_date date,
    invoice_sent date,
    invoice_serial character varying(50),
    invoice_number character varying(50),
    invoice_amount numeric(10,2) DEFAULT 0,
    token character varying(255),
    expires_at timestamp without time zone,
    submitted_at timestamp without time zone
);


ALTER TABLE public.partner_responses OWNER TO neondb_owner;

--
-- Name: partner_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.partner_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_responses_id_seq OWNER TO neondb_owner;

--
-- Name: partner_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.partner_responses_id_seq OWNED BY public.partner_responses.id;


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
-- Name: proposals; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.proposals (
    id integer NOT NULL,
    bid_id integer,
    data jsonb NOT NULL,
    created_by integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.proposals OWNER TO neondb_owner;

--
-- Name: proposals_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.proposals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.proposals_id_seq OWNER TO neondb_owner;

--
-- Name: proposals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.proposals_id_seq OWNED BY public.proposals.id;


--
-- Name: sales; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sales (
    id integer NOT NULL,
    sales_id character varying(50) NOT NULL,
    sales_person character varying(255) NOT NULL,
    contact_person character varying(255) NOT NULL,
    reporting_manager character varying(255) NOT NULL,
    region public.region NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.sales OWNER TO neondb_owner;

--
-- Name: sales_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sales_id_seq OWNER TO neondb_owner;

--
-- Name: sales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sales_id_seq OWNED BY public.sales.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    employee_id character varying(50),
    password_hash character varying(255) NOT NULL,
    role character varying(50) NOT NULL,
    team character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.users OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: vendor_managers; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.vendor_managers (
    id integer NOT NULL,
    vm_id character varying(50) NOT NULL,
    vm_name character varying(255) NOT NULL,
    contact_person character varying(255),
    reporting_manager character varying(255),
    team character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.vendor_managers OWNER TO neondb_owner;

--
-- Name: vendor_managers_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.vendor_managers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vendor_managers_id_seq OWNER TO neondb_owner;

--
-- Name: vendor_managers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.vendor_managers_id_seq OWNED BY public.vendor_managers.id;


--
-- Name: bid_audience_countries id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_audience_countries ALTER COLUMN id SET DEFAULT nextval('public.bid_audience_countries_id_seq'::regclass);


--
-- Name: bid_partners id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_partners ALTER COLUMN id SET DEFAULT nextval('public.bid_partners_id_seq'::regclass);


--
-- Name: bid_po_numbers id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_po_numbers ALTER COLUMN id SET DEFAULT nextval('public.bid_po_numbers_id_seq'::regclass);


--
-- Name: bid_target_audiences id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_target_audiences ALTER COLUMN id SET DEFAULT nextval('public.bid_target_audiences_id_seq'::regclass);


--
-- Name: bids id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bids ALTER COLUMN id SET DEFAULT nextval('public.bids_id_seq'::regclass);


--
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- Name: partner_audience_responses id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_audience_responses ALTER COLUMN id SET DEFAULT nextval('public.partner_audience_responses_id_seq'::regclass);


--
-- Name: partner_links id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_links ALTER COLUMN id SET DEFAULT nextval('public.partner_links_id_seq'::regclass);


--
-- Name: partner_responses id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses ALTER COLUMN id SET DEFAULT nextval('public.partner_responses_id_seq'::regclass);


--
-- Name: partners id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partners ALTER COLUMN id SET DEFAULT nextval('public.partners_id_seq'::regclass);


--
-- Name: proposals id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.proposals ALTER COLUMN id SET DEFAULT nextval('public.proposals_id_seq'::regclass);


--
-- Name: sales id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sales ALTER COLUMN id SET DEFAULT nextval('public.sales_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: vendor_managers id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.vendor_managers ALTER COLUMN id SET DEFAULT nextval('public.vendor_managers_id_seq'::regclass);


--
-- Name: bid_audience_countries bid_audience_countries_bid_id_audience_id_country_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_bid_id_audience_id_country_key UNIQUE (bid_id, audience_id, country);


--
-- Name: bid_audience_countries bid_audience_countries_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_pkey PRIMARY KEY (id);


--
-- Name: bid_partners bid_partners_bid_id_partner_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_bid_id_partner_id_key UNIQUE (bid_id, partner_id);


--
-- Name: bid_partners bid_partners_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_pkey PRIMARY KEY (id);


--
-- Name: bid_po_numbers bid_po_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_po_numbers
    ADD CONSTRAINT bid_po_numbers_pkey PRIMARY KEY (id);


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
-- Name: clients clients_client_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_client_id_key UNIQUE (client_id);


--
-- Name: clients clients_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_email_key UNIQUE (email);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: partner_audience_responses partner_audience_responses_partner_response_id_audience_id__key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_partner_response_id_audience_id__key UNIQUE (partner_response_id, audience_id, country);


--
-- Name: partner_audience_responses partner_audience_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_pkey PRIMARY KEY (id);


--
-- Name: partner_links partner_links_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT partner_links_pkey PRIMARY KEY (id);


--
-- Name: partner_links partner_links_token_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT partner_links_token_key UNIQUE (token);


--
-- Name: partner_responses partner_responses_bid_id_partner_id_loi_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_id_partner_id_loi_key UNIQUE (bid_id, partner_id, loi);


--
-- Name: partner_responses partner_responses_bid_id_partner_id_loi_key1; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_id_partner_id_loi_key1 UNIQUE (bid_id, partner_id, loi);


--
-- Name: partner_responses partner_responses_bid_id_partner_id_loi_key2; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_id_partner_id_loi_key2 UNIQUE (bid_id, partner_id, loi);


--
-- Name: partner_responses partner_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_pkey PRIMARY KEY (id);


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
-- Name: proposals proposals_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_pkey PRIMARY KEY (id);


--
-- Name: sales sales_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_pkey PRIMARY KEY (id);


--
-- Name: sales sales_sales_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_sales_id_key UNIQUE (sales_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_employee_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_employee_id_key UNIQUE (employee_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vendor_managers vendor_managers_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.vendor_managers
    ADD CONSTRAINT vendor_managers_pkey PRIMARY KEY (id);


--
-- Name: vendor_managers vendor_managers_vm_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.vendor_managers
    ADD CONSTRAINT vendor_managers_vm_id_key UNIQUE (vm_id);


--
-- Name: idx_bid_audience_countries_audience_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_bid_audience_countries_audience_id ON public.bid_audience_countries USING btree (audience_id);


--
-- Name: idx_bid_audience_countries_bid_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_bid_audience_countries_bid_id ON public.bid_audience_countries USING btree (bid_id);


--
-- Name: idx_bid_partners_bid_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_bid_partners_bid_id ON public.bid_partners USING btree (bid_id);


--
-- Name: idx_bid_partners_partner_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_bid_partners_partner_id ON public.bid_partners USING btree (partner_id);


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
-- Name: idx_partner_audience_responses_audience_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_partner_audience_responses_audience_id ON public.partner_audience_responses USING btree (audience_id);


--
-- Name: idx_partner_audience_responses_bid_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_partner_audience_responses_bid_id ON public.partner_audience_responses USING btree (bid_id);


--
-- Name: idx_partner_audience_responses_partner_response_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_partner_audience_responses_partner_response_id ON public.partner_audience_responses USING btree (partner_response_id);


--
-- Name: idx_partner_responses_bid_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_partner_responses_bid_id ON public.partner_responses USING btree (bid_id);


--
-- Name: idx_partner_responses_partner_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_partner_responses_partner_id ON public.partner_responses USING btree (partner_id);


--
-- Name: bid_audience_countries bid_audience_countries_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.bid_target_audiences(id) ON DELETE CASCADE;


--
-- Name: bid_audience_countries bid_audience_countries_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- Name: bid_partners bid_partners_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- Name: bid_partners bid_partners_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: bid_po_numbers bid_po_numbers_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bid_po_numbers
    ADD CONSTRAINT bid_po_numbers_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


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
-- Name: partner_audience_responses partner_audience_responses_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.bid_target_audiences(id) ON DELETE CASCADE;


--
-- Name: partner_audience_responses partner_audience_responses_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- Name: partner_audience_responses partner_audience_responses_partner_response_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_partner_response_id_fkey FOREIGN KEY (partner_response_id) REFERENCES public.partner_responses(id) ON DELETE CASCADE;


--
-- Name: partner_links partner_links_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT partner_links_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- Name: partner_links partner_links_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT partner_links_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: partner_responses partner_responses_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- Name: partner_responses partner_responses_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: proposals proposals_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- Name: proposals proposals_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

