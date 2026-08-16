--
-- PostgreSQL database dump
--

\restrict r9ATOgMUvrINkPHWXQhLXuhGaqtFh5w7ygWVbrjq5AwgymMfmodIhU7k1EbpsDv

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

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

ALTER TABLE IF EXISTS ONLY public.shop_trade DROP CONSTRAINT IF EXISTS shop_trade_trade_id_fkey;
ALTER TABLE IF EXISTS ONLY public.shop_trade DROP CONSTRAINT IF EXISTS shop_trade_shop_id_fkey;
ALTER TABLE IF EXISTS ONLY public.employee DROP CONSTRAINT IF EXISTS employee_branch_id_fkey;
ALTER TABLE IF EXISTS ONLY public.branch DROP CONSTRAINT IF EXISTS branch_shop_id_fkey;
ALTER TABLE IF EXISTS ONLY public.trade DROP CONSTRAINT IF EXISTS trade_pkey;
ALTER TABLE IF EXISTS ONLY public.trade DROP CONSTRAINT IF EXISTS trade_name_en_key;
ALTER TABLE IF EXISTS ONLY public.trade DROP CONSTRAINT IF EXISTS trade_name_ar_key;
ALTER TABLE IF EXISTS ONLY public.shop_trade DROP CONSTRAINT IF EXISTS shop_trade_pkey;
ALTER TABLE IF EXISTS ONLY public.shop DROP CONSTRAINT IF EXISTS shop_pkey;
ALTER TABLE IF EXISTS ONLY public.shop DROP CONSTRAINT IF EXISTS shop_commercial_register_key;
ALTER TABLE IF EXISTS ONLY public.employee DROP CONSTRAINT IF EXISTS employee_pkey;
ALTER TABLE IF EXISTS ONLY public.employee DROP CONSTRAINT IF EXISTS employee_national_id_key;
ALTER TABLE IF EXISTS ONLY public.branch DROP CONSTRAINT IF EXISTS branch_pkey;
ALTER TABLE IF EXISTS public.trade ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.shop ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.employee ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.branch ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.trade_id_seq;
DROP TABLE IF EXISTS public.trade;
DROP TABLE IF EXISTS public.shop_trade;
DROP SEQUENCE IF EXISTS public.shop_id_seq;
DROP TABLE IF EXISTS public.shop;
DROP SEQUENCE IF EXISTS public.employee_id_seq;
DROP TABLE IF EXISTS public.employee;
DROP SEQUENCE IF EXISTS public.branch_id_seq;
DROP TABLE IF EXISTS public.branch;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: branch; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.branch (
    id integer NOT NULL,
    shop_id integer NOT NULL,
    address text NOT NULL,
    branch_name text,
    phone_number character varying(15) NOT NULL,
    CONSTRAINT branch_phone_number_check CHECK (((phone_number)::text ~ '^\+?[0-9]{7,15}$'::text))
);


--
-- Name: branch_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.branch_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: branch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.branch_id_seq OWNED BY public.branch.id;


--
-- Name: employee; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employee (
    id integer NOT NULL,
    name_ar text NOT NULL,
    name_en text,
    branch_id integer NOT NULL,
    national_id text,
    phone_number character varying(15) NOT NULL,
    CONSTRAINT employee_national_id_check CHECK ((national_id ~ '^[0-9]{14}$'::text)),
    CONSTRAINT employee_phone_number_check CHECK (((phone_number)::text ~ '^\+?[0-9]{7,15}$'::text))
);


--
-- Name: employee_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employee_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.employee_id_seq OWNED BY public.employee.id;


--
-- Name: shop; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shop (
    id integer NOT NULL,
    name_en text,
    name_ar text NOT NULL,
    commercial_register text,
    bank_account text,
    technical_capacity text
);


--
-- Name: shop_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shop_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shop_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shop_id_seq OWNED BY public.shop.id;


--
-- Name: shop_trade; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shop_trade (
    shop_id integer NOT NULL,
    trade_id integer NOT NULL
);


--
-- Name: trade; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trade (
    id integer NOT NULL,
    name_en text NOT NULL,
    name_ar text NOT NULL
);


--
-- Name: trade_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trade_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trade_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trade_id_seq OWNED BY public.trade.id;


--
-- Name: branch id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch ALTER COLUMN id SET DEFAULT nextval('public.branch_id_seq'::regclass);


--
-- Name: employee id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee ALTER COLUMN id SET DEFAULT nextval('public.employee_id_seq'::regclass);


--
-- Name: shop id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shop ALTER COLUMN id SET DEFAULT nextval('public.shop_id_seq'::regclass);


--
-- Name: trade id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trade ALTER COLUMN id SET DEFAULT nextval('public.trade_id_seq'::regclass);


--
-- Data for Name: branch; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.branch (id, shop_id, address, branch_name, phone_number) FROM stdin;
1	1	شارع عباس العقاد، مدينة نصر، القاهرة	فرع مدينة نصر	01001234567
2	1	شارع 9، المعادي، القاهرة	فرع المعادي	01001234568
3	2	شارع فيصل، الجيزة	فرع فيصل	01112345670
4	2	المحور المركزي، 6 أكتوبر	فرع أكتوبر	01112345671
5	3	شارع مصطفى النحاس، مدينة نصر، القاهرة	فرع مدينة نصر	01223456780
6	3	شارع المنشية، حلوان، القاهرة	فرع حلوان	01223456781
7	4	شارع الهرم، الجيزة	فرع الهرم	01004567890
8	5	شارع شبرا، القاهرة	فرع شبرا	01015678901
9	6	شارع الترعة، إمبابة، الجيزة	\N	01126789012
10	7	شارع الزيتون، القاهرة	\N	01237890123
11	8	شارع جامعة الدول العربية، المهندسين، الجيزة	الفرع الرئيسي	0233445566
12	8	شارع الطيران، مدينة نصر، القاهرة	فرع مدينة نصر	01008901234
13	8	شارع فؤاد، الإسكندرية	فرع الإسكندرية	0334455667
\.


--
-- Data for Name: employee; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.employee (id, name_ar, name_en, branch_id, national_id, phone_number) FROM stdin;
1	محمد عبد الرحمن	Mohamed Abdelrahman	1	28505121201234	01001111001
2	أحمد سيد	\N	1	29103150102345	01001111002
3	إبراهيم فتحي	\N	2	28812200203456	01001111003
4	مصطفى كامل	\N	3	29407081304567	01001111004
5	يوسف عادل	\N	4	29612110105678	01001111005
6	خالد منصور	Khaled Mansour	5	28402251206789	01001111006
7	طارق حسن	\N	5	29009030207890	01001111007
8	عمرو زكي	\N	6	29205171308901	01001111008
9	سامح رمضان	\N	7	28710290109012	01001111009
10	وليد نبيل	\N	7	29308140210123	01001111010
11	هاني جرجس	\N	8	28601061211234	01001111011
12	سيد عبد العزيز	\N	9	\N	01126789012
13	رضا شعبان	\N	10	\N	01237890123
14	شريف الديب	Sherif Eldeeb	11	28203190112345	01001111014
15	نورا سليم	Nora Selim	11	29511240213456	01001111015
16	تامر عبد الله	\N	12	29102080114567	01001111016
17	محمود بدر	\N	13	28909120215678	01001111017
\.


--
-- Data for Name: shop; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.shop (id, name_en, name_ar, commercial_register, bank_account, technical_capacity) FROM stdin;
1	Al-Nour Plumbing	مؤسسة النور للسباكة	45219	1002334577891	3 فنيين وسيارة نقل
2	Al-Herafy Carpentry	ورشة الحرفي للنجارة	38714	1002334578402	ورشة مجهزة و4 نجارين
3	Al-Shorouk Electrical	الشروق للأعمال الكهربائية	52063	1002334579115	5 فنيين معتمدين
4	Al-Mohandes Motors	مركز المهندس للميكانيكا	29845	1002334580336	ورشة كبرى و8 ميكانيكيين
5	Al-Amana Metalwork	حدادة الأمانة	61402	1002334581247	\N
6	\N	عم سيد للأعمال المنزلية	\N	\N	فرد واحد
7	Al-Fannan Painting	نقاشة الفنان	\N	1002334583092	نقاش و2 مساعدين
8	Al-Itqan Maintenance	شركة الإتقان للصيانة المتكاملة	70318	1002334584661	شركة، 20 فني، 3 سيارات
\.


--
-- Data for Name: shop_trade; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.shop_trade (shop_id, trade_id) FROM stdin;
1	1
2	2
3	3
4	4
5	5
6	6
7	7
8	1
8	3
8	5
\.


--
-- Data for Name: trade; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.trade (id, name_en, name_ar) FROM stdin;
1	Plumbing	السباكة
2	Carpentry	النجارة
3	Electrical	الكهرباء
4	Mechanical	اعمال ميكانيكا
5	Metalwork	حدادة
6	Domestic Services	اعمال منزلية
7	Painting	نقاشة
\.


--
-- Name: branch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.branch_id_seq', 16, true);


--
-- Name: employee_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.employee_id_seq', 20, true);


--
-- Name: shop_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.shop_id_seq', 12, true);


--
-- Name: trade_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.trade_id_seq', 10, true);


--
-- Name: branch branch_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch
    ADD CONSTRAINT branch_pkey PRIMARY KEY (id);


--
-- Name: employee employee_national_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_national_id_key UNIQUE (national_id);


--
-- Name: employee employee_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_pkey PRIMARY KEY (id);


--
-- Name: shop shop_commercial_register_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shop
    ADD CONSTRAINT shop_commercial_register_key UNIQUE (commercial_register);


--
-- Name: shop shop_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shop
    ADD CONSTRAINT shop_pkey PRIMARY KEY (id);


--
-- Name: shop_trade shop_trade_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shop_trade
    ADD CONSTRAINT shop_trade_pkey PRIMARY KEY (shop_id, trade_id);


--
-- Name: trade trade_name_ar_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trade
    ADD CONSTRAINT trade_name_ar_key UNIQUE (name_ar);


--
-- Name: trade trade_name_en_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trade
    ADD CONSTRAINT trade_name_en_key UNIQUE (name_en);


--
-- Name: trade trade_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trade
    ADD CONSTRAINT trade_pkey PRIMARY KEY (id);


--
-- Name: branch branch_shop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.branch
    ADD CONSTRAINT branch_shop_id_fkey FOREIGN KEY (shop_id) REFERENCES public.shop(id) ON DELETE CASCADE;


--
-- Name: employee employee_branch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employee
    ADD CONSTRAINT employee_branch_id_fkey FOREIGN KEY (branch_id) REFERENCES public.branch(id) ON DELETE CASCADE;


--
-- Name: shop_trade shop_trade_shop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shop_trade
    ADD CONSTRAINT shop_trade_shop_id_fkey FOREIGN KEY (shop_id) REFERENCES public.shop(id) ON DELETE CASCADE;


--
-- Name: shop_trade shop_trade_trade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shop_trade
    ADD CONSTRAINT shop_trade_trade_id_fkey FOREIGN KEY (trade_id) REFERENCES public.trade(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict r9ATOgMUvrINkPHWXQhLXuhGaqtFh5w7ygWVbrjq5AwgymMfmodIhU7k1EbpsDv

