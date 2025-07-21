--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.4

-- Started on 2025-05-09 21:07:55

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 876 (class 1247 OID 16398)
-- Name: bid_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.bid_status AS ENUM (
    'draft',
    'submitted',
    'infield',
    'closure',
    'ready_for_invoice',
    'invoiced',
    'rejected'
);


ALTER TYPE public.bid_status OWNER TO postgres;

--
-- TOC entry 879 (class 1247 OID 16412)
-- Name: methodology; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.methodology AS ENUM (
    'online',
    'offline',
    'mixed',
    'quant'
);


ALTER TYPE public.methodology OWNER TO postgres;

--
-- TOC entry 873 (class 1247 OID 16388)
-- Name: region; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.region AS ENUM (
    'north',
    'south',
    'east',
    'west'
);


ALTER TYPE public.region OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 232 (class 1259 OID 16538)
-- Name: bid_audience_countries; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.bid_audience_countries OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 16537)
-- Name: bid_audience_countries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bid_audience_countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_audience_countries_id_seq OWNER TO postgres;

--
-- TOC entry 5122 (class 0 OID 0)
-- Dependencies: 231
-- Name: bid_audience_countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_audience_countries_id_seq OWNED BY public.bid_audience_countries.id;


--
-- TOC entry 234 (class 1259 OID 16559)
-- Name: bid_partners; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bid_partners (
    id integer NOT NULL,
    bid_id integer,
    partner_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    token character varying(255),
    expires_at timestamp without time zone,
    submitted_at timestamp without time zone
);


ALTER TABLE public.bid_partners OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 16558)
-- Name: bid_partners_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bid_partners_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_partners_id_seq OWNER TO postgres;

--
-- TOC entry 5123 (class 0 OID 0)
-- Dependencies: 233
-- Name: bid_partners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_partners_id_seq OWNED BY public.bid_partners.id;


--
-- TOC entry 236 (class 1259 OID 16580)
-- Name: bid_po_numbers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bid_po_numbers (
    id integer NOT NULL,
    bid_id integer,
    po_number character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.bid_po_numbers OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 16579)
-- Name: bid_po_numbers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bid_po_numbers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_po_numbers_id_seq OWNER TO postgres;

--
-- TOC entry 5124 (class 0 OID 0)
-- Dependencies: 235
-- Name: bid_po_numbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_po_numbers_id_seq OWNED BY public.bid_po_numbers.id;


--
-- TOC entry 230 (class 1259 OID 16522)
-- Name: bid_target_audiences; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.bid_target_audiences OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16521)
-- Name: bid_target_audiences_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bid_target_audiences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_target_audiences_id_seq OWNER TO postgres;

--
-- TOC entry 5125 (class 0 OID 0)
-- Dependencies: 229
-- Name: bid_target_audiences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_target_audiences_id_seq OWNED BY public.bid_target_audiences.id;


--
-- TOC entry 228 (class 1259 OID 16493)
-- Name: bids; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bids (
    id integer NOT NULL,
    bid_number character varying(50) NOT NULL,
    bid_date date NOT NULL,
    study_name character varying(255) NOT NULL,
    methodology public.methodology NOT NULL,
    status public.bid_status DEFAULT 'draft'::public.bid_status,
    client integer,
    sales_contact integer,
    vm_contact integer,
    project_requirement text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    rejection_reason character varying(100),
    rejection_comments text
);


ALTER TABLE public.bids OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16492)
-- Name: bids_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bids_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bids_id_seq OWNER TO postgres;

--
-- TOC entry 5126 (class 0 OID 0)
-- Dependencies: 227
-- Name: bids_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bids_id_seq OWNED BY public.bids.id;


--
-- TOC entry 220 (class 1259 OID 16435)
-- Name: clients; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.clients OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16434)
-- Name: clients_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.clients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clients_id_seq OWNER TO postgres;

--
-- TOC entry 5127 (class 0 OID 0)
-- Dependencies: 219
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- TOC entry 240 (class 1259 OID 16622)
-- Name: partner_audience_responses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partner_audience_responses (
    id integer NOT NULL,
    bid_id integer,
    partner_response_id integer,
    audience_id integer,
    country character varying(100) NOT NULL,
    allocation integer DEFAULT 0 NOT NULL,
    commitment integer DEFAULT 0,
    cpi numeric(10,2) DEFAULT 0,
    timeline_days integer DEFAULT 0,
    comments text DEFAULT ''::text,
    n_delivered integer DEFAULT 0,
    quality_rejects integer DEFAULT 0,
    final_loi numeric(5,2),
    final_ir numeric(5,2),
    final_timeline integer,
    final_cpi numeric(10,2),
    field_close_date date,
    initial_cost numeric(10,2) DEFAULT 0,
    final_cost numeric(10,2) DEFAULT 0,
    savings numeric(10,2) DEFAULT 0,
    communication text,
    engagement text,
    problem_solving text,
    additional_feedback text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_best_efforts boolean DEFAULT false,
    commitment_type character varying(10) DEFAULT 'fixed'::character varying,
    CONSTRAINT partner_audience_responses_commitment_type_check CHECK (((commitment_type)::text = ANY ((ARRAY['fixed'::character varying, 'be_max'::character varying])::text[])))
);


ALTER TABLE public.partner_audience_responses OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 16621)
-- Name: partner_audience_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.partner_audience_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_audience_responses_id_seq OWNER TO postgres;

--
-- TOC entry 5128 (class 0 OID 0)
-- Dependencies: 239
-- Name: partner_audience_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partner_audience_responses_id_seq OWNED BY public.partner_audience_responses.id;


--
-- TOC entry 242 (class 1259 OID 25180)
-- Name: partner_links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partner_links (
    id integer NOT NULL,
    bid_id integer NOT NULL,
    partner_id integer NOT NULL,
    token character varying(255) NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    submitted_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.partner_links OWNER TO postgres;

--
-- TOC entry 241 (class 1259 OID 25179)
-- Name: partner_links_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.partner_links_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_links_id_seq OWNER TO postgres;

--
-- TOC entry 5129 (class 0 OID 0)
-- Dependencies: 241
-- Name: partner_links_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partner_links_id_seq OWNED BY public.partner_links.id;


--
-- TOC entry 238 (class 1259 OID 16594)
-- Name: partner_responses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partner_responses (
    id integer NOT NULL,
    bid_id integer,
    partner_id integer,
    loi integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying,
    currency character varying(3) DEFAULT 'USD'::character varying,
    pmf numeric(5,2) DEFAULT 0,
    timeline integer DEFAULT 0,
    invoice_date date,
    invoice_sent date,
    invoice_serial character varying(50),
    invoice_number character varying(50),
    invoice_amount numeric(10,2) DEFAULT 0,
    response_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    token character varying(255),
    expires_at timestamp without time zone,
    submitted_at timestamp without time zone
);


ALTER TABLE public.partner_responses OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 16593)
-- Name: partner_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.partner_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_responses_id_seq OWNER TO postgres;

--
-- TOC entry 5130 (class 0 OID 0)
-- Dependencies: 237
-- Name: partner_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partner_responses_id_seq OWNED BY public.partner_responses.id;


--
-- TOC entry 226 (class 1259 OID 16476)
-- Name: partners; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partners (
    id integer NOT NULL,
    partner_id character varying(100) NOT NULL,
    partner_name character varying(255) NOT NULL,
    contact_person character varying(255) NOT NULL,
    contact_email character varying(255) NOT NULL,
    contact_phone character varying(100) DEFAULT 'NA'::character varying,
    website character varying(255),
    company_address text DEFAULT 'NA'::text,
    specialized text[],
    geographic_coverage text[],
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.partners OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16475)
-- Name: partners_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.partners_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partners_id_seq OWNER TO postgres;

--
-- TOC entry 5131 (class 0 OID 0)
-- Dependencies: 225
-- Name: partners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partners_id_seq OWNED BY public.partners.id;


--
-- TOC entry 244 (class 1259 OID 25201)
-- Name: proposals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.proposals (
    id integer NOT NULL,
    bid_id integer,
    data jsonb NOT NULL,
    created_by integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.proposals OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 25200)
-- Name: proposals_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.proposals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.proposals_id_seq OWNER TO postgres;

--
-- TOC entry 5132 (class 0 OID 0)
-- Dependencies: 243
-- Name: proposals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.proposals_id_seq OWNED BY public.proposals.id;


--
-- TOC entry 222 (class 1259 OID 16450)
-- Name: sales; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.sales OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16449)
-- Name: sales_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sales_id_seq OWNER TO postgres;

--
-- TOC entry 5133 (class 0 OID 0)
-- Dependencies: 221
-- Name: sales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sales_id_seq OWNED BY public.sales.id;


--
-- TOC entry 218 (class 1259 OID 16420)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16419)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 5134 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 224 (class 1259 OID 16463)
-- Name: vendor_managers; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE public.vendor_managers OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16462)
-- Name: vendor_managers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vendor_managers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vendor_managers_id_seq OWNER TO postgres;

--
-- TOC entry 5135 (class 0 OID 0)
-- Dependencies: 223
-- Name: vendor_managers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vendor_managers_id_seq OWNED BY public.vendor_managers.id;


--
-- TOC entry 4841 (class 2604 OID 16541)
-- Name: bid_audience_countries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries ALTER COLUMN id SET DEFAULT nextval('public.bid_audience_countries_id_seq'::regclass);


--
-- TOC entry 4845 (class 2604 OID 16562)
-- Name: bid_partners id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners ALTER COLUMN id SET DEFAULT nextval('public.bid_partners_id_seq'::regclass);


--
-- TOC entry 4848 (class 2604 OID 16583)
-- Name: bid_po_numbers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_po_numbers ALTER COLUMN id SET DEFAULT nextval('public.bid_po_numbers_id_seq'::regclass);


--
-- TOC entry 4837 (class 2604 OID 16525)
-- Name: bid_target_audiences id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_target_audiences ALTER COLUMN id SET DEFAULT nextval('public.bid_target_audiences_id_seq'::regclass);


--
-- TOC entry 4833 (class 2604 OID 16496)
-- Name: bids id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids ALTER COLUMN id SET DEFAULT nextval('public.bids_id_seq'::regclass);


--
-- TOC entry 4819 (class 2604 OID 16438)
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- TOC entry 4861 (class 2604 OID 16625)
-- Name: partner_audience_responses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses ALTER COLUMN id SET DEFAULT nextval('public.partner_audience_responses_id_seq'::regclass);


--
-- TOC entry 4876 (class 2604 OID 25183)
-- Name: partner_links id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_links ALTER COLUMN id SET DEFAULT nextval('public.partner_links_id_seq'::regclass);


--
-- TOC entry 4851 (class 2604 OID 16597)
-- Name: partner_responses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses ALTER COLUMN id SET DEFAULT nextval('public.partner_responses_id_seq'::regclass);


--
-- TOC entry 4828 (class 2604 OID 16479)
-- Name: partners id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partners ALTER COLUMN id SET DEFAULT nextval('public.partners_id_seq'::regclass);


--
-- TOC entry 4877 (class 2604 OID 25204)
-- Name: proposals id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proposals ALTER COLUMN id SET DEFAULT nextval('public.proposals_id_seq'::regclass);


--
-- TOC entry 4822 (class 2604 OID 16453)
-- Name: sales id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales ALTER COLUMN id SET DEFAULT nextval('public.sales_id_seq'::regclass);


--
-- TOC entry 4816 (class 2604 OID 16423)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4825 (class 2604 OID 16466)
-- Name: vendor_managers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_managers ALTER COLUMN id SET DEFAULT nextval('public.vendor_managers_id_seq'::regclass);


--
-- TOC entry 4918 (class 2606 OID 16547)
-- Name: bid_audience_countries bid_audience_countries_bid_id_audience_id_country_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_bid_id_audience_id_country_key UNIQUE (bid_id, audience_id, country);


--
-- TOC entry 4920 (class 2606 OID 16545)
-- Name: bid_audience_countries bid_audience_countries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_pkey PRIMARY KEY (id);


--
-- TOC entry 4924 (class 2606 OID 16568)
-- Name: bid_partners bid_partners_bid_id_partner_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_bid_id_partner_id_key UNIQUE (bid_id, partner_id);


--
-- TOC entry 4926 (class 2606 OID 16566)
-- Name: bid_partners bid_partners_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_pkey PRIMARY KEY (id);


--
-- TOC entry 4928 (class 2606 OID 25176)
-- Name: bid_partners bid_partners_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_token_key UNIQUE (token);


--
-- TOC entry 4932 (class 2606 OID 16587)
-- Name: bid_po_numbers bid_po_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_po_numbers
    ADD CONSTRAINT bid_po_numbers_pkey PRIMARY KEY (id);


--
-- TOC entry 4915 (class 2606 OID 16531)
-- Name: bid_target_audiences bid_target_audiences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_target_audiences
    ADD CONSTRAINT bid_target_audiences_pkey PRIMARY KEY (id);


--
-- TOC entry 4908 (class 2606 OID 16505)
-- Name: bids bids_bid_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_bid_number_key UNIQUE (bid_number);


--
-- TOC entry 4910 (class 2606 OID 16503)
-- Name: bids bids_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_pkey PRIMARY KEY (id);


--
-- TOC entry 4888 (class 2606 OID 16446)
-- Name: clients clients_client_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_client_id_key UNIQUE (client_id);


--
-- TOC entry 4890 (class 2606 OID 16448)
-- Name: clients clients_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_email_key UNIQUE (email);


--
-- TOC entry 4892 (class 2606 OID 16444)
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- TOC entry 4945 (class 2606 OID 16641)
-- Name: partner_audience_responses partner_audience_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_pkey PRIMARY KEY (id);


--
-- TOC entry 4949 (class 2606 OID 25185)
-- Name: partner_links partner_links_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT partner_links_pkey PRIMARY KEY (id);


--
-- TOC entry 4951 (class 2606 OID 25187)
-- Name: partner_links partner_links_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT partner_links_token_key UNIQUE (token);


--
-- TOC entry 4936 (class 2606 OID 16610)
-- Name: partner_responses partner_responses_bid_id_partner_id_loi_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_id_partner_id_loi_key UNIQUE (bid_id, partner_id, loi);


--
-- TOC entry 4938 (class 2606 OID 16608)
-- Name: partner_responses partner_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_pkey PRIMARY KEY (id);


--
-- TOC entry 4940 (class 2606 OID 25178)
-- Name: partner_responses partner_responses_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_token_key UNIQUE (token);


--
-- TOC entry 4902 (class 2606 OID 16491)
-- Name: partners partners_contact_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_contact_email_key UNIQUE (contact_email);


--
-- TOC entry 4904 (class 2606 OID 16489)
-- Name: partners partners_partner_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_partner_id_key UNIQUE (partner_id);


--
-- TOC entry 4906 (class 2606 OID 16487)
-- Name: partners partners_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_pkey PRIMARY KEY (id);


--
-- TOC entry 4953 (class 2606 OID 25210)
-- Name: proposals proposals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_pkey PRIMARY KEY (id);


--
-- TOC entry 4894 (class 2606 OID 16459)
-- Name: sales sales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_pkey PRIMARY KEY (id);


--
-- TOC entry 4896 (class 2606 OID 16461)
-- Name: sales sales_sales_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_sales_id_key UNIQUE (sales_id);


--
-- TOC entry 4947 (class 2606 OID 25199)
-- Name: partner_audience_responses unique_bid_partner_audience_country; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT unique_bid_partner_audience_country UNIQUE (bid_id, partner_response_id, audience_id, country);


--
-- TOC entry 4882 (class 2606 OID 16431)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4884 (class 2606 OID 16433)
-- Name: users users_employee_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_employee_id_key UNIQUE (employee_id);


--
-- TOC entry 4886 (class 2606 OID 16429)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4898 (class 2606 OID 16472)
-- Name: vendor_managers vendor_managers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_managers
    ADD CONSTRAINT vendor_managers_pkey PRIMARY KEY (id);


--
-- TOC entry 4900 (class 2606 OID 16474)
-- Name: vendor_managers vendor_managers_vm_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_managers
    ADD CONSTRAINT vendor_managers_vm_id_key UNIQUE (vm_id);


--
-- TOC entry 4921 (class 1259 OID 16662)
-- Name: idx_bid_audience_countries_audience_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bid_audience_countries_audience_id ON public.bid_audience_countries USING btree (audience_id);


--
-- TOC entry 4922 (class 1259 OID 16661)
-- Name: idx_bid_audience_countries_bid_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bid_audience_countries_bid_id ON public.bid_audience_countries USING btree (bid_id);


--
-- TOC entry 4929 (class 1259 OID 16663)
-- Name: idx_bid_partners_bid_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bid_partners_bid_id ON public.bid_partners USING btree (bid_id);


--
-- TOC entry 4930 (class 1259 OID 16664)
-- Name: idx_bid_partners_partner_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bid_partners_partner_id ON public.bid_partners USING btree (partner_id);


--
-- TOC entry 4916 (class 1259 OID 16660)
-- Name: idx_bid_target_audiences_bid_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bid_target_audiences_bid_id ON public.bid_target_audiences USING btree (bid_id);


--
-- TOC entry 4911 (class 1259 OID 16657)
-- Name: idx_bids_client; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bids_client ON public.bids USING btree (client);


--
-- TOC entry 4912 (class 1259 OID 16658)
-- Name: idx_bids_sales_contact; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bids_sales_contact ON public.bids USING btree (sales_contact);


--
-- TOC entry 4913 (class 1259 OID 16659)
-- Name: idx_bids_vm_contact; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bids_vm_contact ON public.bids USING btree (vm_contact);


--
-- TOC entry 4941 (class 1259 OID 16668)
-- Name: idx_partner_audience_responses_audience_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_partner_audience_responses_audience_id ON public.partner_audience_responses USING btree (audience_id);


--
-- TOC entry 4942 (class 1259 OID 16667)
-- Name: idx_partner_audience_responses_bid_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_partner_audience_responses_bid_id ON public.partner_audience_responses USING btree (bid_id);


--
-- TOC entry 4943 (class 1259 OID 16669)
-- Name: idx_partner_audience_responses_partner_response_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_partner_audience_responses_partner_response_id ON public.partner_audience_responses USING btree (partner_response_id);


--
-- TOC entry 4933 (class 1259 OID 16665)
-- Name: idx_partner_responses_bid_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_partner_responses_bid_id ON public.partner_responses USING btree (bid_id);


--
-- TOC entry 4934 (class 1259 OID 16666)
-- Name: idx_partner_responses_partner_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_partner_responses_partner_id ON public.partner_responses USING btree (partner_id);


--
-- TOC entry 4958 (class 2606 OID 16553)
-- Name: bid_audience_countries bid_audience_countries_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.bid_target_audiences(id) ON DELETE CASCADE;


--
-- TOC entry 4959 (class 2606 OID 16548)
-- Name: bid_audience_countries bid_audience_countries_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4960 (class 2606 OID 16569)
-- Name: bid_partners bid_partners_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4961 (class 2606 OID 16574)
-- Name: bid_partners bid_partners_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- TOC entry 4962 (class 2606 OID 16588)
-- Name: bid_po_numbers bid_po_numbers_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_po_numbers
    ADD CONSTRAINT bid_po_numbers_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4957 (class 2606 OID 16532)
-- Name: bid_target_audiences bid_target_audiences_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_target_audiences
    ADD CONSTRAINT bid_target_audiences_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4954 (class 2606 OID 16506)
-- Name: bids bids_client_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_client_fkey FOREIGN KEY (client) REFERENCES public.clients(id);


--
-- TOC entry 4955 (class 2606 OID 16511)
-- Name: bids bids_sales_contact_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_sales_contact_fkey FOREIGN KEY (sales_contact) REFERENCES public.sales(id);


--
-- TOC entry 4956 (class 2606 OID 16516)
-- Name: bids bids_vm_contact_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_vm_contact_fkey FOREIGN KEY (vm_contact) REFERENCES public.vendor_managers(id);


--
-- TOC entry 4968 (class 2606 OID 25188)
-- Name: partner_links fk_bid; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT fk_bid FOREIGN KEY (bid_id) REFERENCES public.bids(id);


--
-- TOC entry 4969 (class 2606 OID 25193)
-- Name: partner_links fk_partner; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT fk_partner FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- TOC entry 4965 (class 2606 OID 16652)
-- Name: partner_audience_responses partner_audience_responses_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.bid_target_audiences(id) ON DELETE CASCADE;


--
-- TOC entry 4966 (class 2606 OID 16642)
-- Name: partner_audience_responses partner_audience_responses_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4967 (class 2606 OID 16647)
-- Name: partner_audience_responses partner_audience_responses_partner_response_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_partner_response_id_fkey FOREIGN KEY (partner_response_id) REFERENCES public.partner_responses(id) ON DELETE CASCADE;


--
-- TOC entry 4963 (class 2606 OID 16611)
-- Name: partner_responses partner_responses_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4964 (class 2606 OID 16616)
-- Name: partner_responses partner_responses_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- TOC entry 4970 (class 2606 OID 25211)
-- Name: proposals proposals_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4971 (class 2606 OID 25216)
-- Name: proposals proposals_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


-- Completed on 2025-05-09 21:07:57

--
-- PostgreSQL database dump complete
--

