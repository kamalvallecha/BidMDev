--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

-- Started on 2025-03-31 17:36:18

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
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 5080 (class 0 OID 0)
-- Dependencies: 4
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- TOC entry 884 (class 1247 OID 29796)
-- Name: bidstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.bidstatus AS ENUM (
    'DRAFT',
    'SUBMITTED',
    'IN_REVIEW',
    'APPROVED',
    'REJECTED'
);


ALTER TYPE public.bidstatus OWNER TO postgres;

--
-- TOC entry 917 (class 1247 OID 30617)
-- Name: methodology; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.methodology AS ENUM (
    'quant',
    'qual',
    'both'
);


ALTER TYPE public.methodology OWNER TO postgres;

--
-- TOC entry 932 (class 1247 OID 30738)
-- Name: mode_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.mode_type AS ENUM (
    'Online',
    'Offline',
    'Both'
);


ALTER TYPE public.mode_type OWNER TO postgres;

--
-- TOC entry 893 (class 1247 OID 29988)
-- Name: region; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.region AS ENUM (
    'north',
    'south',
    'east',
    'west'
);


ALTER TYPE public.region OWNER TO postgres;

--
-- TOC entry 929 (class 1247 OID 30729)
-- Name: ta_category; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.ta_category AS ENUM (
    'B2B',
    'B2C',
    'HC - HCP',
    'HC - Patient'
);


ALTER TYPE public.ta_category OWNER TO postgres;

--
-- TOC entry 920 (class 1247 OID 30654)
-- Name: userrole; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userrole AS ENUM (
    'admin',
    'user',
    'manager'
);


ALTER TYPE public.userrole OWNER TO postgres;

--
-- TOC entry 926 (class 1247 OID 30670)
-- Name: userstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userstatus AS ENUM (
    'active',
    'inactive'
);


ALTER TYPE public.userstatus OWNER TO postgres;

--
-- TOC entry 923 (class 1247 OID 30662)
-- Name: userteam; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userteam AS ENUM (
    'sales',
    'marketing',
    'engineering'
);


ALTER TYPE public.userteam OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 242 (class 1259 OID 32861)
-- Name: bid_audience_countries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bid_audience_countries (
    id integer NOT NULL,
    bid_id integer,
    audience_id integer,
    country text NOT NULL,
    sample_size integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.bid_audience_countries OWNER TO postgres;

--
-- TOC entry 241 (class 1259 OID 32860)
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
-- TOC entry 5081 (class 0 OID 0)
-- Dependencies: 241
-- Name: bid_audience_countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_audience_countries_id_seq OWNED BY public.bid_audience_countries.id;


--
-- TOC entry 251 (class 1259 OID 41044)
-- Name: bid_countries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bid_countries (
    id integer NOT NULL,
    bid_id integer,
    country character varying(100) NOT NULL,
    sample_size integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.bid_countries OWNER TO postgres;

--
-- TOC entry 250 (class 1259 OID 41043)
-- Name: bid_countries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bid_countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_countries_id_seq OWNER TO postgres;

--
-- TOC entry 5082 (class 0 OID 0)
-- Dependencies: 250
-- Name: bid_countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_countries_id_seq OWNED BY public.bid_countries.id;


--
-- TOC entry 240 (class 1259 OID 32832)
-- Name: bid_loi; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bid_loi (
    id integer NOT NULL,
    bid_id integer,
    loi integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.bid_loi OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 32831)
-- Name: bid_loi_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bid_loi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_loi_id_seq OWNER TO postgres;

--
-- TOC entry 5083 (class 0 OID 0)
-- Dependencies: 239
-- Name: bid_loi_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_loi_id_seq OWNED BY public.bid_loi.id;


--
-- TOC entry 249 (class 1259 OID 41042)
-- Name: bid_number_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bid_number_seq
    START WITH 40000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bid_number_seq OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 32814)
-- Name: bid_partners; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bid_partners (
    id integer NOT NULL,
    bid_id integer,
    partner_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    pmf numeric(10,2),
    currency character varying(10)
);


ALTER TABLE public.bid_partners OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 32813)
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
-- TOC entry 5084 (class 0 OID 0)
-- Dependencies: 237
-- Name: bid_partners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_partners_id_seq OWNED BY public.bid_partners.id;


--
-- TOC entry 248 (class 1259 OID 34690)
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
-- TOC entry 247 (class 1259 OID 34689)
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
-- TOC entry 5085 (class 0 OID 0)
-- Dependencies: 247
-- Name: bid_po_numbers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_po_numbers_id_seq OWNED BY public.bid_po_numbers.id;


--
-- TOC entry 236 (class 1259 OID 32798)
-- Name: bid_target_audiences; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bid_target_audiences (
    id integer NOT NULL,
    bid_id integer,
    audience_name text NOT NULL,
    ta_category public.ta_category NOT NULL,
    broader_category text NOT NULL,
    exact_ta_definition text NOT NULL,
    mode public.mode_type NOT NULL,
    sample_required integer NOT NULL,
    ir integer NOT NULL,
    comments text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    country_samples jsonb DEFAULT '{}'::jsonb
);


ALTER TABLE public.bid_target_audiences OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 32797)
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
-- TOC entry 5086 (class 0 OID 0)
-- Dependencies: 235
-- Name: bid_target_audiences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bid_target_audiences_id_seq OWNED BY public.bid_target_audiences.id;


--
-- TOC entry 234 (class 1259 OID 32769)
-- Name: bids; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bids (
    id integer NOT NULL,
    bid_number character varying(50) NOT NULL,
    bid_date date NOT NULL,
    study_name character varying(255) NOT NULL,
    methodology public.methodology NOT NULL,
    sales_contact integer,
    vm_contact integer,
    client integer,
    project_requirement text NOT NULL,
    comments text,
    status character varying(50) DEFAULT 'draft'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.bids OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 32768)
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
-- TOC entry 5087 (class 0 OID 0)
-- Dependencies: 233
-- Name: bids_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bids_id_seq OWNED BY public.bids.id;


--
-- TOC entry 230 (class 1259 OID 30257)
-- Name: clients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clients (
    id integer NOT NULL,
    client_id character varying(50) NOT NULL,
    client_name character varying(100) NOT NULL,
    contact_person character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(20) NOT NULL,
    country character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.clients OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 30256)
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
-- TOC entry 5088 (class 0 OID 0)
-- Dependencies: 229
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- TOC entry 246 (class 1259 OID 34525)
-- Name: partner_audience_responses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partner_audience_responses (
    id integer NOT NULL,
    partner_response_id integer,
    bid_id integer,
    audience_id integer,
    country text NOT NULL,
    commitment integer NOT NULL,
    cpi numeric(10,2) NOT NULL,
    timeline_days integer DEFAULT 0 NOT NULL,
    comments text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    allocation integer DEFAULT 0,
    quality_reject boolean DEFAULT false,
    field_close_date date,
    ir numeric(5,2),
    n_delivered integer DEFAULT 0,
    final_loi integer,
    final_ir numeric(5,2),
    final_timeline integer,
    quality_rejects integer,
    communication_rating integer,
    engagement_rating integer,
    problem_solving_rating integer,
    additional_feedback text,
    final_cpi numeric(10,2),
    initial_cost numeric(10,2),
    final_cost numeric(10,2),
    savings numeric(10,2)
);


ALTER TABLE public.partner_audience_responses OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 34524)
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
-- TOC entry 5089 (class 0 OID 0)
-- Dependencies: 245
-- Name: partner_audience_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partner_audience_responses_id_seq OWNED BY public.partner_audience_responses.id;


--
-- TOC entry 244 (class 1259 OID 32904)
-- Name: partner_response_countries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partner_response_countries (
    id integer NOT NULL,
    response_id integer,
    audience_id integer,
    country text NOT NULL,
    commitment integer NOT NULL,
    cpi numeric(10,2) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.partner_response_countries OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 32903)
-- Name: partner_response_countries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.partner_response_countries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.partner_response_countries_id_seq OWNER TO postgres;

--
-- TOC entry 5090 (class 0 OID 0)
-- Dependencies: 243
-- Name: partner_response_countries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partner_response_countries_id_seq OWNED BY public.partner_response_countries.id;


--
-- TOC entry 232 (class 1259 OID 31348)
-- Name: partner_responses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partner_responses (
    id integer NOT NULL,
    bid_id integer,
    partner_id integer,
    loi integer NOT NULL,
    currency character varying(3) NOT NULL,
    pmf numeric(10,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) DEFAULT 'draft'::character varying,
    quality_rejects integer DEFAULT 0,
    communication_rating integer DEFAULT 0,
    engagement_rating integer DEFAULT 0,
    problem_solving_rating integer DEFAULT 0,
    additional_feedback text DEFAULT ''::text,
    timeline integer DEFAULT 0,
    final_loi integer,
    final_ir numeric(5,2),
    final_timeline integer,
    invoice_date date,
    invoice_sent date,
    invoice_serial character varying(50),
    invoice_number character varying(50),
    invoice_amount numeric(10,2),
    timeline_days integer DEFAULT 0,
    ir numeric(5,2) DEFAULT 0
);


ALTER TABLE public.partner_responses OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 31347)
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
-- TOC entry 5091 (class 0 OID 0)
-- Dependencies: 231
-- Name: partner_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partner_responses_id_seq OWNED BY public.partner_responses.id;


--
-- TOC entry 253 (class 1259 OID 41068)
-- Name: partners; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.partners (
    id integer NOT NULL,
    partner_id character varying(50) NOT NULL,
    partner_name character varying(100) NOT NULL,
    contact_person character varying(100) NOT NULL,
    contact_email character varying(100) NOT NULL,
    contact_phone character varying(20) NOT NULL,
    website character varying(200),
    company_address text NOT NULL,
    specialized text[] NOT NULL,
    geographic_coverage text[] NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.partners OWNER TO postgres;

--
-- TOC entry 252 (class 1259 OID 41067)
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
-- TOC entry 5092 (class 0 OID 0)
-- Dependencies: 252
-- Name: partners_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.partners_id_seq OWNED BY public.partners.id;


--
-- TOC entry 226 (class 1259 OID 29845)
-- Name: sales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sales (
    id integer NOT NULL,
    sales_id character varying,
    sales_person character varying,
    contact_person character varying,
    reporting_manager character varying,
    region character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.sales OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 29844)
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
-- TOC entry 5093 (class 0 OID 0)
-- Dependencies: 225
-- Name: sales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sales_id_seq OWNED BY public.sales.id;


--
-- TOC entry 255 (class 1259 OID 49729)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(50) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    employee_id character varying(50),
    team character varying(50) DEFAULT 'Operations'::character varying NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 254 (class 1259 OID 49728)
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
-- TOC entry 5094 (class 0 OID 0)
-- Dependencies: 254
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 228 (class 1259 OID 29857)
-- Name: vendor_managers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vendor_managers (
    id integer NOT NULL,
    vm_id character varying,
    vm_name character varying,
    contact_person character varying,
    team character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    reporting_manager character varying(100)
);


ALTER TABLE public.vendor_managers OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 29856)
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
-- TOC entry 5095 (class 0 OID 0)
-- Dependencies: 227
-- Name: vendor_managers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vendor_managers_id_seq OWNED BY public.vendor_managers.id;


--
-- TOC entry 4827 (class 2604 OID 32864)
-- Name: bid_audience_countries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries ALTER COLUMN id SET DEFAULT nextval('public.bid_audience_countries_id_seq'::regclass);


--
-- TOC entry 4842 (class 2604 OID 41047)
-- Name: bid_countries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_countries ALTER COLUMN id SET DEFAULT nextval('public.bid_countries_id_seq'::regclass);


--
-- TOC entry 4825 (class 2604 OID 32835)
-- Name: bid_loi id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_loi ALTER COLUMN id SET DEFAULT nextval('public.bid_loi_id_seq'::regclass);


--
-- TOC entry 4823 (class 2604 OID 32817)
-- Name: bid_partners id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners ALTER COLUMN id SET DEFAULT nextval('public.bid_partners_id_seq'::regclass);


--
-- TOC entry 4839 (class 2604 OID 34693)
-- Name: bid_po_numbers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_po_numbers ALTER COLUMN id SET DEFAULT nextval('public.bid_po_numbers_id_seq'::regclass);


--
-- TOC entry 4819 (class 2604 OID 32801)
-- Name: bid_target_audiences id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_target_audiences ALTER COLUMN id SET DEFAULT nextval('public.bid_target_audiences_id_seq'::regclass);


--
-- TOC entry 4815 (class 2604 OID 32772)
-- Name: bids id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids ALTER COLUMN id SET DEFAULT nextval('public.bids_id_seq'::regclass);


--
-- TOC entry 4800 (class 2604 OID 30260)
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- TOC entry 4832 (class 2604 OID 34528)
-- Name: partner_audience_responses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses ALTER COLUMN id SET DEFAULT nextval('public.partner_audience_responses_id_seq'::regclass);


--
-- TOC entry 4830 (class 2604 OID 32907)
-- Name: partner_response_countries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_response_countries ALTER COLUMN id SET DEFAULT nextval('public.partner_response_countries_id_seq'::regclass);


--
-- TOC entry 4803 (class 2604 OID 31351)
-- Name: partner_responses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses ALTER COLUMN id SET DEFAULT nextval('public.partner_responses_id_seq'::regclass);


--
-- TOC entry 4846 (class 2604 OID 41071)
-- Name: partners id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partners ALTER COLUMN id SET DEFAULT nextval('public.partners_id_seq'::regclass);


--
-- TOC entry 4798 (class 2604 OID 29848)
-- Name: sales id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales ALTER COLUMN id SET DEFAULT nextval('public.sales_id_seq'::regclass);


--
-- TOC entry 4849 (class 2604 OID 49732)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4799 (class 2604 OID 29860)
-- Name: vendor_managers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_managers ALTER COLUMN id SET DEFAULT nextval('public.vendor_managers_id_seq'::regclass);


--
-- TOC entry 4886 (class 2606 OID 32870)
-- Name: bid_audience_countries bid_audience_countries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_pkey PRIMARY KEY (id);


--
-- TOC entry 4888 (class 2606 OID 38125)
-- Name: bid_audience_countries bid_audience_countries_unique_constraint; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_unique_constraint UNIQUE (bid_id, audience_id, country);


--
-- TOC entry 4900 (class 2606 OID 41054)
-- Name: bid_countries bid_countries_bid_id_country_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_countries
    ADD CONSTRAINT bid_countries_bid_id_country_key UNIQUE (bid_id, country);


--
-- TOC entry 4902 (class 2606 OID 41052)
-- Name: bid_countries bid_countries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_countries
    ADD CONSTRAINT bid_countries_pkey PRIMARY KEY (id);


--
-- TOC entry 4884 (class 2606 OID 32838)
-- Name: bid_loi bid_loi_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_loi
    ADD CONSTRAINT bid_loi_pkey PRIMARY KEY (id);


--
-- TOC entry 4882 (class 2606 OID 32820)
-- Name: bid_partners bid_partners_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_pkey PRIMARY KEY (id);


--
-- TOC entry 4898 (class 2606 OID 34697)
-- Name: bid_po_numbers bid_po_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_po_numbers
    ADD CONSTRAINT bid_po_numbers_pkey PRIMARY KEY (id);


--
-- TOC entry 4880 (class 2606 OID 32807)
-- Name: bid_target_audiences bid_target_audiences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_target_audiences
    ADD CONSTRAINT bid_target_audiences_pkey PRIMARY KEY (id);


--
-- TOC entry 4876 (class 2606 OID 32781)
-- Name: bids bids_bid_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_bid_number_key UNIQUE (bid_number);


--
-- TOC entry 4878 (class 2606 OID 32779)
-- Name: bids bids_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_pkey PRIMARY KEY (id);


--
-- TOC entry 4864 (class 2606 OID 30268)
-- Name: clients clients_client_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_client_id_key UNIQUE (client_id);


--
-- TOC entry 4866 (class 2606 OID 30270)
-- Name: clients clients_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_email_key UNIQUE (email);


--
-- TOC entry 4868 (class 2606 OID 30266)
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- TOC entry 4892 (class 2606 OID 34534)
-- Name: partner_audience_responses partner_audience_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_pkey PRIMARY KEY (id);


--
-- TOC entry 4894 (class 2606 OID 36339)
-- Name: partner_audience_responses partner_audience_responses_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_unique UNIQUE (partner_response_id, audience_id, country);


--
-- TOC entry 4896 (class 2606 OID 38430)
-- Name: partner_audience_responses partner_audience_responses_unique_constraint; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_unique_constraint UNIQUE (bid_id, partner_response_id, audience_id, country);


--
-- TOC entry 4890 (class 2606 OID 32912)
-- Name: partner_response_countries partner_response_countries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_response_countries
    ADD CONSTRAINT partner_response_countries_pkey PRIMARY KEY (id);


--
-- TOC entry 4870 (class 2606 OID 31358)
-- Name: partner_responses partner_responses_bid_id_partner_id_loi_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_id_partner_id_loi_key UNIQUE (bid_id, partner_id, loi);


--
-- TOC entry 4872 (class 2606 OID 36249)
-- Name: partner_responses partner_responses_bid_partner_loi_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_partner_loi_unique UNIQUE (bid_id, partner_id, loi);


--
-- TOC entry 4874 (class 2606 OID 31356)
-- Name: partner_responses partner_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_pkey PRIMARY KEY (id);


--
-- TOC entry 4904 (class 2606 OID 41081)
-- Name: partners partners_contact_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_contact_email_key UNIQUE (contact_email);


--
-- TOC entry 4906 (class 2606 OID 41079)
-- Name: partners partners_partner_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_partner_id_key UNIQUE (partner_id);


--
-- TOC entry 4908 (class 2606 OID 41077)
-- Name: partners partners_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_pkey PRIMARY KEY (id);


--
-- TOC entry 4857 (class 2606 OID 29852)
-- Name: sales sales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_pkey PRIMARY KEY (id);


--
-- TOC entry 4910 (class 2606 OID 49740)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4912 (class 2606 OID 49742)
-- Name: users users_employee_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_employee_id_key UNIQUE (employee_id);


--
-- TOC entry 4914 (class 2606 OID 49738)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4862 (class 2606 OID 29864)
-- Name: vendor_managers vendor_managers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_managers
    ADD CONSTRAINT vendor_managers_pkey PRIMARY KEY (id);


--
-- TOC entry 4853 (class 1259 OID 29853)
-- Name: ix_sales_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sales_id ON public.sales USING btree (id);


--
-- TOC entry 4854 (class 1259 OID 29854)
-- Name: ix_sales_sales_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_sales_sales_id ON public.sales USING btree (sales_id);


--
-- TOC entry 4855 (class 1259 OID 29855)
-- Name: ix_sales_sales_person; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sales_sales_person ON public.sales USING btree (sales_person);


--
-- TOC entry 4858 (class 1259 OID 29866)
-- Name: ix_vendor_managers_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_vendor_managers_id ON public.vendor_managers USING btree (id);


--
-- TOC entry 4859 (class 1259 OID 29867)
-- Name: ix_vendor_managers_vm_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_vendor_managers_vm_id ON public.vendor_managers USING btree (vm_id);


--
-- TOC entry 4860 (class 1259 OID 29865)
-- Name: ix_vendor_managers_vm_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_vendor_managers_vm_name ON public.vendor_managers USING btree (vm_name);


--
-- TOC entry 4921 (class 2606 OID 32876)
-- Name: bid_audience_countries bid_audience_countries_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.bid_target_audiences(id) ON DELETE CASCADE;


--
-- TOC entry 4922 (class 2606 OID 32871)
-- Name: bid_audience_countries bid_audience_countries_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_audience_countries
    ADD CONSTRAINT bid_audience_countries_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4929 (class 2606 OID 41055)
-- Name: bid_countries bid_countries_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_countries
    ADD CONSTRAINT bid_countries_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4920 (class 2606 OID 32839)
-- Name: bid_loi bid_loi_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_loi
    ADD CONSTRAINT bid_loi_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4919 (class 2606 OID 32821)
-- Name: bid_partners bid_partners_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_partners
    ADD CONSTRAINT bid_partners_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4928 (class 2606 OID 34698)
-- Name: bid_po_numbers bid_po_numbers_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_po_numbers
    ADD CONSTRAINT bid_po_numbers_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4918 (class 2606 OID 32808)
-- Name: bid_target_audiences bid_target_audiences_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bid_target_audiences
    ADD CONSTRAINT bid_target_audiences_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4915 (class 2606 OID 32792)
-- Name: bids bids_client_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_client_fkey FOREIGN KEY (client) REFERENCES public.clients(id);


--
-- TOC entry 4916 (class 2606 OID 32782)
-- Name: bids bids_sales_contact_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_sales_contact_fkey FOREIGN KEY (sales_contact) REFERENCES public.sales(id);


--
-- TOC entry 4917 (class 2606 OID 32787)
-- Name: bids bids_vm_contact_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_vm_contact_fkey FOREIGN KEY (vm_contact) REFERENCES public.vendor_managers(id);


--
-- TOC entry 4925 (class 2606 OID 34545)
-- Name: partner_audience_responses partner_audience_responses_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.bid_target_audiences(id);


--
-- TOC entry 4926 (class 2606 OID 34540)
-- Name: partner_audience_responses partner_audience_responses_bid_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id) ON DELETE CASCADE;


--
-- TOC entry 4927 (class 2606 OID 34535)
-- Name: partner_audience_responses partner_audience_responses_partner_response_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_partner_response_id_fkey FOREIGN KEY (partner_response_id) REFERENCES public.partner_responses(id) ON DELETE CASCADE;


--
-- TOC entry 4923 (class 2606 OID 32918)
-- Name: partner_response_countries partner_response_countries_audience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_response_countries
    ADD CONSTRAINT partner_response_countries_audience_id_fkey FOREIGN KEY (audience_id) REFERENCES public.bid_target_audiences(id);


--
-- TOC entry 4924 (class 2606 OID 32913)
-- Name: partner_response_countries partner_response_countries_response_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.partner_response_countries
    ADD CONSTRAINT partner_response_countries_response_id_fkey FOREIGN KEY (response_id) REFERENCES public.partner_responses(id) ON DELETE CASCADE;


-- Completed on 2025-03-31 17:36:18

--
-- PostgreSQL database dump complete
--

