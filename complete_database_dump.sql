--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8
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
-- Name: bid_status_new; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.bid_status_new AS ENUM (
    'draft',
    'infield',
    'closure',
    'ready_for_invoice',
    'invoiced',
    'completed',
    'rejected'
);


ALTER TYPE public.bid_status_new OWNER TO neondb_owner;

--
-- Name: methodology; Type: TYPE; Schema: public; Owner: neondb_owner
--

CREATE TYPE public.methodology AS ENUM (
    'online',
    'offline',
    'mixed'
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
    is_best_efforts boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    is_best_efforts boolean DEFAULT false,
    ir numeric(5,2),
    comments text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    bid_id integer,
    partner_response_id integer,
    audience_id integer,
    country character varying(100) NOT NULL,
    allocation integer DEFAULT 0 NOT NULL,
    commitment integer DEFAULT 0,
    is_best_efforts boolean DEFAULT false,
    commitment_type character varying(10) DEFAULT 'fixed'::character varying,
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
    CONSTRAINT partner_audience_responses_commitment_type_check CHECK (((commitment_type)::text = ANY ((ARRAY['fixed'::character varying, 'be_max'::character varying])::text[])))
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
    token text NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    notification_sent boolean DEFAULT false
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
-- Data for Name: bid_audience_countries; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.bid_audience_countries (id, bid_id, audience_id, country, sample_size, is_best_efforts, created_at) FROM stdin;
39	1	1	Afghanistan	100	f	2025-05-13 12:51:48.656898
40	1	1	Albania	100	f	2025-05-13 12:51:48.656898
41	1	1	Algeria	0	t	2025-05-13 12:51:48.656898
42	1	2	Afghanistan	100	f	2025-05-13 12:51:48.656898
43	1	2	Albania	0	t	2025-05-13 12:51:48.656898
44	1	2	Algeria	400	f	2025-05-13 12:51:48.656898
\.


--
-- Data for Name: bid_partners; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.bid_partners (id, bid_id, partner_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: bid_po_numbers; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.bid_po_numbers (id, bid_id, po_number, created_at, updated_at) FROM stdin;
1	1	111	2025-05-12 13:28:21.981823	2025-05-12 13:28:21.981823
\.


--
-- Data for Name: bid_target_audiences; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.bid_target_audiences (id, bid_id, audience_name, ta_category, broader_category, exact_ta_definition, mode, sample_required, is_best_efforts, ir, comments, created_at, updated_at) FROM stdin;
1	1	Audience - 1	B2B	Advertiser/Marketing/Media DM	addddddddddddddd	Online	0	t	12.00	BE/Max	2025-05-12 12:58:28.714852	2025-05-13 12:51:48.656898
2	1	Audience - 2	B2B	Advertiser/Marketing/Media DM	ad	CATI	500	f	20.00	Sample	2025-05-12 13:17:52.706791	2025-05-13 12:51:48.656898
\.


--
-- Data for Name: bids; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.bids (id, bid_number, bid_date, study_name, methodology, status, client, sales_contact, vm_contact, project_requirement, created_at, updated_at, rejection_reason, rejection_comments) FROM stdin;
1	40000	2025-05-12	K11	offline	closure	1	1	1	KV11	2025-05-12 12:58:28.714852	2025-05-13 12:51:48.656898	\N	\N
\.


--
-- Data for Name: clients; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.clients (id, client_id, client_name, contact_person, email, phone, country, created_at, updated_at) FROM stdin;
1	C5i_1	Vritual Causway	Bill	bill@vc.com	88888881	USA	2025-04-07 18:53:17.29629	2025-04-09 01:40:11.017104
\.


--
-- Data for Name: partner_audience_responses; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.partner_audience_responses (id, bid_id, partner_response_id, audience_id, country, allocation, commitment, is_best_efforts, commitment_type, cpi, timeline_days, comments, n_delivered, quality_rejects, final_loi, final_ir, final_timeline, final_cpi, field_close_date, initial_cost, final_cost, savings, communication, engagement, problem_solving, additional_feedback, created_at, updated_at) FROM stdin;
17	1	3	2	Albania	10	99	f	fixed	99.00	99	99	10	7	7.00	7.00	7	28.00	2025-05-11	0.00	280.00	710.00	3	3	3	sdsds	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
4	1	2	1	Albania	10	99	f	fixed	99.00	99	99	9	9	9.00	9.00	9	22.00	2025-05-11	0.00	198.00	693.00	1	1	1	ooopo	2025-05-12 12:59:07.766199	2025-05-12 13:24:49.346676
3	1	2	1	Afghanistan	10	0	t	be_max	99.00	99	99	9	9	9.00	9.00	9	25.00	2025-05-11	0.00	225.00	666.00	1	1	1	ooopo	2025-05-12 12:59:07.766199	2025-05-12 13:24:49.346676
10	1	2	2	Afghanistan	10	99	f	fixed	99.00	99	99	7	7	7.00	7.00	7	25.00	2025-05-11	0.00	175.00	518.00	2	2	2	rtrtr	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
1	1	1	1	Afghanistan	0	99	f	fixed	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 12:58:51.164674	2025-05-12 13:24:49.346676
5	1	1	1	Algeria	0	99	f	fixed	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
6	1	1	2	Afghanistan	0	0	t	be_max	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
2	1	1	1	Albania	30	0	t	be_max	99.00	99	99	25	5	5.00	5.00	5	10.00	2025-05-11	0.00	250.00	2225.00	1	1	1	sdsds	2025-05-12 12:58:51.164674	2025-05-12 13:24:49.346676
23	1	4	2	Albania	10	0	t	be_max	88.00	88	88	0	9	9.00	9.00	9	\N	2025-05-11	0.00	0.00	0.00	1	1	3	wewew	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
19	1	4	1	Afghanistan	10	0	t	be_max	88.00	88	88	10	5	5.00	5.00	5	12.00	2025-05-11	0.00	120.00	760.00	1	1	1	sdssd	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
22	1	4	2	Afghanistan	10	88	f	fixed	88.00	88	88	10	9	9.00	9.00	9	10.00	2025-05-11	0.00	100.00	780.00	1	1	3	wewew	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
13	1	3	1	Afghanistan	10	0	t	be_max	99.00	99	99	10	9	9.00	9.00	9	28.00	2025-05-11	0.00	280.00	710.00	2	2	2	sdsd	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
16	1	3	2	Afghanistan	10	99	f	fixed	99.00	99	99	10	7	7.00	7.00	7	28.00	2025-05-11	0.00	280.00	710.00	3	3	3	sdsds	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
7	1	1	2	Albania	0	99	f	fixed	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
8	1	1	2	Algeria	0	0	t	be_max	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
9	1	2	1	Algeria	0	0	t	be_max	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
11	1	2	2	Albania	0	99	f	fixed	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
12	1	2	2	Algeria	0	0	t	be_max	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
14	1	3	1	Albania	0	0	t	be_max	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
15	1	3	1	Algeria	0	99	f	fixed	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
18	1	3	2	Algeria	0	99	f	fixed	99.00	99	99	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
20	1	4	1	Albania	0	88	f	fixed	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
21	1	4	1	Algeria	0	0	t	be_max	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
24	1	4	2	Algeria	0	0	t	be_max	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
25	1	5	1	Afghanistan	0	88	f	fixed	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
26	1	5	1	Albania	0	0	t	be_max	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
27	1	5	1	Algeria	0	0	t	be_max	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
28	1	5	2	Afghanistan	0	0	t	be_max	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
35	1	6	2	Albania	0	0	t	be_max	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
36	1	6	2	Algeria	0	88	f	fixed	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
33	1	6	1	Algeria	10	0	t	be_max	88.00	88	88	10	7	7.00	7.00	7	20.00	2025-05-11	0.00	200.00	680.00	1	1	1	ffdfd	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
32	1	6	1	Albania	10	88	f	fixed	88.00	88	88	10	7	7.00	7.00	7	20.00	2025-05-11	0.00	200.00	680.00	1	1	1	ffdfd	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
34	1	6	2	Afghanistan	10	0	t	be_max	88.00	88	88	10	9	9.00	9.00	9	22.00	2025-05-11	0.00	220.00	660.00	2	3	2	tytyt	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
29	1	5	2	Albania	50	88	f	fixed	88.00	88	88	40	6	6.00	6.00	6	12.00	2025-05-11	0.00	480.00	3040.00	1	1	1	ssdsd	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
30	1	5	2	Algeria	0	88	f	fixed	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
31	1	6	1	Afghanistan	0	88	f	fixed	88.00	88	88	0	0	\N	\N	\N	\N	\N	0.00	0.00	0.00	\N	\N	\N	\N	2025-05-12 13:17:52.706791	2025-05-12 13:24:49.346676
\.


--
-- Data for Name: partner_links; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.partner_links (id, bid_id, partner_id, token, expires_at, created_at, updated_at, notification_sent) FROM stdin;
1	1	1	ype2kv-tjTPNwA-F-ake-hjhsFkRdCSYne0_r12rFDI	2025-06-11 17:27:49.313667	2025-05-12 17:27:48.767683	2025-05-12 17:27:48.767683	f
2	1	2	BP-jcIo3ElGTzRaznjUmLl1BAazeXhDSStCyL8uCg9k	2025-06-11 20:32:14.485971	2025-05-12 20:32:13.904964	2025-05-12 20:32:13.904964	f
\.


--
-- Data for Name: partner_responses; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.partner_responses (id, bid_id, partner_id, loi, status, currency, pmf, timeline, invoice_date, invoice_sent, invoice_serial, invoice_number, invoice_amount, response_date, created_at, updated_at, token, expires_at, submitted_at) FROM stdin;
1	1	1	1	draft	USD	100.00	0	2025-05-12	2025-05-12	777	666	250.00	2025-05-12 12:58:31.524664	2025-05-12 12:58:31.524664	2025-05-13 12:51:48.656898	\N	\N	\N
2	1	1	2	draft	USD	100.00	0	2025-05-12	2025-05-12	777	666	598.00	2025-05-12 12:58:31.524664	2025-05-12 12:58:31.524664	2025-05-13 12:51:48.656898	\N	\N	\N
3	1	1	3	draft	USD	100.00	0	2025-05-12	2025-05-12	777	666	840.00	2025-05-12 13:17:52.706791	2025-05-12 13:17:52.706791	2025-05-13 12:51:48.656898	\N	\N	\N
4	1	2	1	draft	USD	200.00	0	2025-05-12	2025-05-12	999	888	220.00	2025-05-12 13:17:52.706791	2025-05-12 13:17:52.706791	2025-05-13 12:51:48.656898	\N	\N	\N
5	1	2	2	draft	USD	200.00	0	2025-05-12	2025-05-12	999	888	480.00	2025-05-12 13:17:52.706791	2025-05-12 13:17:52.706791	2025-05-13 12:51:48.656898	\N	\N	\N
6	1	2	3	draft	USD	200.00	0	2025-05-12	2025-05-12	999	888	620.00	2025-05-12 13:17:52.706791	2025-05-12 13:17:52.706791	2025-05-13 12:51:48.656898	\N	\N	\N
\.


--
-- Data for Name: partners; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.partners (id, partner_id, partner_name, contact_person, contact_email, contact_phone, website, company_address, specialized, geographic_coverage, created_at, updated_at) FROM stdin;
2	CSi_Partner_2	Rakuten	Kapil Bajaj	kapil.bajaj@rakuten.com	9319199513	www.insight.rakuten.com	LOGIX PARK, A - 4 & 5, 2nd Floor,Sector  16, NOIDA,Uttar Pradesh  201301, INDIA O: 91-120-4111258	{B2B,B2C}	{India}	2025-04-07 18:41:14.166666	2025-04-07 18:41:14.166666
3	CSi_Partner_3	Dynata India	Hemant Deo	Hemant.Deo@Dynata.com	9848788808	www.dynata.com	Dynata, 10th Floor, Building 14-B DLF  |  Gurgaon, HR,  122002, India\n	{B2B,B2C}	{India}	2025-04-07 18:41:52.312808	2025-04-07 20:36:44.171793
1	CSi_Partner_1	Toluna	Barnali Saikia	barnali.saikia@toluna.com	9711745582	www.tolunacorporate.com	9th Floor IT SEZ Park, Sector 59, Gurugram, Haryana India\n	{B2B,B2C,"HC - HCP"}	{India}	2025-04-07 18:36:27.200507	2025-04-09 01:24:04.179347
\.


--
-- Data for Name: proposals; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.proposals (id, bid_id, data, created_by, created_at, updated_at) FROM stdin;
1	1	{"data": {"bidInfo": {"bidNumber": "40000", "studyName": "K11", "clientName": "Vritual Causway", "methodology": "offline"}, "summary": {"avgCPI": "99.00", "totalCost": "15840.00", "totalMargin": "6336.00", "partnersUsed": 1, "totalRevenue": "22176.00", "totalCompletes": "160", "effectiveMargin": "28.57"}, "allocations": {"1": {"Algeria": {"1": {"cpi": 99, "cost": "7920.00", "revenue": "11088.00", "selected": true, "timeline": "", "allocation": "80", "commitment": 99, "salesPrice": "138.60"}}, "Afghanistan": {"1": {"cpi": 99, "cost": "7920.00", "revenue": "11088.00", "selected": true, "timeline": "", "allocation": "80", "commitment": 99, "salesPrice": "138.60"}}}}, "marginPercentage": 40}, "bid_id": 1}	\N	2025-05-13 13:44:28.903147	2025-05-13 13:45:15.690309
\.


--
-- Data for Name: sales; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.sales (id, sales_id, sales_person, contact_person, reporting_manager, region, created_at, updated_at) FROM stdin;
1	100036	Shrikant Sunchu	shrikant.sunchu@c5i.ai	Varun Vig	north	2025-04-07 18:52:42.383336	2025-04-09 01:43:29.359355
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.users (id, email, name, employee_id, password_hash, role, team, created_at, updated_at) FROM stdin;
1	admin@example.com	Admin User	ADMIN001	$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW	admin	Administration	2025-05-09 15:44:45.153634	2025-05-09 15:44:45.153634
2	sales@example.com	Sales User	SALES001	$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW	sales	Sales	2025-05-09 15:44:45.153634	2025-05-09 15:44:45.153634
3	vm@example.com	VM User	VM001	$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW	VM	Vendor Management	2025-05-09 15:44:45.153634	2025-05-09 15:44:45.153634
4	pm@example.com	PM User	PM001	$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW	PM	Project Management	2025-05-09 15:44:45.153634	2025-05-09 15:44:45.153634
\.


--
-- Data for Name: vendor_managers; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.vendor_managers (id, vm_id, vm_name, contact_person, reporting_manager, team, created_at, updated_at) FROM stdin;
1	100015	Ruturaj Shridhar Mohite	ruturaj.mohite@c5i.ai	Sumanto Dutta	pod4	2025-05-09 17:59:24.219875	2025-05-09 17:59:24.219875
\.


--
-- Name: bid_audience_countries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.bid_audience_countries_id_seq', 44, true);


--
-- Name: bid_partners_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.bid_partners_id_seq', 1, false);


--
-- Name: bid_po_numbers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.bid_po_numbers_id_seq', 1, true);


--
-- Name: bid_target_audiences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.bid_target_audiences_id_seq', 2, true);


--
-- Name: bids_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.bids_id_seq', 1, true);


--
-- Name: clients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.clients_id_seq', 1, false);


--
-- Name: partner_audience_responses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.partner_audience_responses_id_seq', 36, true);


--
-- Name: partner_links_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.partner_links_id_seq', 2, true);


--
-- Name: partner_responses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.partner_responses_id_seq', 6, true);


--
-- Name: partners_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.partners_id_seq', 1, false);


--
-- Name: proposals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.proposals_id_seq', 1, true);


--
-- Name: sales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.sales_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: vendor_managers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.vendor_managers_id_seq', 1, true);


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
-- Name: partner_audience_responses partner_audience_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_audience_responses
    ADD CONSTRAINT partner_audience_responses_pkey PRIMARY KEY (id);


--
-- Name: partner_links partner_links_bid_id_partner_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT partner_links_bid_id_partner_id_key UNIQUE (bid_id, partner_id);


--
-- Name: partner_links partner_links_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_links
    ADD CONSTRAINT partner_links_pkey PRIMARY KEY (id);


--
-- Name: partner_responses partner_responses_bid_id_partner_id_loi_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_bid_id_partner_id_loi_key UNIQUE (bid_id, partner_id, loi);


--
-- Name: partner_responses partner_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_pkey PRIMARY KEY (id);


--
-- Name: partner_responses partner_responses_token_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partner_responses
    ADD CONSTRAINT partner_responses_token_key UNIQUE (token);


--
-- Name: partners partners_contact_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_contact_email_key UNIQUE (contact_email);


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
-- Name: bids bids_vm_contact_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.bids
    ADD CONSTRAINT bids_vm_contact_fkey FOREIGN KEY (vm_contact) REFERENCES public.vendor_managers(id);


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
    ADD CONSTRAINT partner_links_bid_id_fkey FOREIGN KEY (bid_id) REFERENCES public.bids(id);


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

