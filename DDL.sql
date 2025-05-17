-- Unknown how to generate base type type

alter type gtrgm owner to postgres;

create table collections
(
    id                  integer,
    itemid              integer,
    pubtown             varchar,
    pagesnumber         integer,
    titleadditionalinfo varchar,
    volumename          varchar,
    edn                 varchar,
    seriesname          varchar,
    yearpublished       integer,
    placepublished      varchar,
    publisher           varchar,
    responsibility      varchar,
    seriesnumber        varchar,
    isbn                varchar,
    volumenumber        varchar,
    doi                 varchar
);

alter table collections
    owner to myuser;

create table abstracts
(
    itemid   integer,
    language varchar,
    content  text
);

alter table abstracts
    owner to myuser;

create table item_codes
(
    itemid   integer,
    codetype varchar,
    value    varchar
);

alter table item_codes
    owner to myuser;

create table journal_issues
(
    journalid  integer,
    contnumber varchar,
    number     varchar,
    year       integer,
    volume     varchar
);

alter table journal_issues
    owner to myuser;

create table citing_data
(
    authorid          integer,
    citingpublication varchar,
    authorpublication varchar
);

alter table citing_data
    owner to myuser;

create table authors
(
    id       integer,
    itemid   integer,
    num      integer,
    authorid integer,
    language varchar,
    status   integer,
    lastname varchar,
    initials varchar,
    email    varchar
);

alter table authors
    owner to myuser;

create index idx_authors_authorid
    on authors (authorid);

create index idx_authors_itemid
    on authors (itemid);

create index idx_authors_num
    on authors (num);

create index idx_authors_status
    on authors (status);

create index idx_authors_language_upper
    on authors (upper(language::text));

create index idx_authors_email_trgm
    on authors using gin (email gin_trgm_ops);

create index idx_authors_lastname_trgm
    on authors using gin (lastname gin_trgm_ops);

create index idx_authors_initials_trgm
    on authors using gin (initials gin_trgm_ops);

create table journals
(
    id           integer,
    itemid       integer,
    journalid    integer,
    issn         varchar,
    eissn        varchar,
    impactfactor double precision,
    vak          varchar,
    scopus       varchar,
    webofscience varchar,
    rsci         varchar,
    countryid    varchar,
    name         varchar
);

alter table journals
    owner to myuser;

create table conference_titles
(
    conferenceid integer,
    language     varchar,
    title        varchar
);

alter table conference_titles
    owner to myuser;

create table elibrary_organizations
(
    countryid        varchar,
    organizationid   integer,
    organizationname varchar
);

alter table elibrary_organizations
    owner to myuser;

create index idx_elibrary_organizations_orgid
    on elibrary_organizations (organizationid);

create index idx_elibrary_organizations_countryid
    on elibrary_organizations (upper(countryid::text));

create index idx_elibrary_organizations_name_trgm
    on elibrary_organizations using gin (organizationname gin_trgm_ops);

create index idx_elibrary_orgs_orgid
    on elibrary_organizations (organizationid);

create table coordinate_data
(
    region           varchar,
    municipality     varchar,
    settlement       varchar,
    "latitude(dms)"  varchar,
    "longitude(dms)" varchar,
    "latitude(dd)"   double precision,
    "longitude(dd)"  double precision
);

alter table coordinate_data
    owner to myuser;

create table reference_data
(
    itemid             integer,
    referencenumber    integer,
    subreferencenumber integer,
    targetid           integer,
    text               varchar
);

alter table reference_data
    owner to myuser;

create table items
(
    itemid             integer,
    genreid            varchar,
    typecode           varchar,
    language           varchar,
    mainrubriccode     integer,
    oecdcode           integer,
    cited              integer,
    corecited          integer,
    risc               varchar,
    corerisc           varchar,
    parentid           integer,
    isft               integer,
    isnew              integer,
    title              varchar,
    year               integer,
    volume             integer,
    pages              varchar,
    pagesnumber        integer,
    dateinstall        timestamp,
    ref                varchar,
    link               varchar,
    grnti              integer,
    edn                varchar,
    isbn               varchar,
    placeofpublication varchar
);

alter table items
    owner to myuser;

create index idx_items_itemid
    on items (itemid);

create index idx_items_title_trgm
    on items using gin (title gin_trgm_ops);

create index idx_items_isbn_trgm
    on items using gin (isbn gin_trgm_ops);

create index idx_items_placeofpublication_trgm
    on items using gin (placeofpublication gin_trgm_ops);

create index idx_items_year
    on items (year);

create index idx_items_genreid
    on items (genreid);

create index idx_items_typecode
    on items (typecode);

create index idx_items_language_upper
    on items (upper(language::text));

create table conferences
(
    id                  integer,
    itemid              integer,
    seriesnumber        varchar,
    seriesname          varchar,
    volumenumber        varchar,
    volumename          varchar,
    pagesnumber         integer,
    placeofpublication  varchar,
    responsibility      varchar,
    doi                 varchar,
    additionaltitleinfo varchar,
    conferencesponsor   varchar,
    edition             varchar,
    isbn                varchar,
    publicationtown     varchar,
    yearofpublication   integer,
    publisher           varchar,
    conferencename      varchar,
    conferenceplace     varchar,
    conferencestartdate date,
    conferenceenddate   date
);

alter table conferences
    owner to myuser;

create table keywords
(
    itemid   integer,
    language varchar,
    keyword  varchar
);

alter table keywords
    owner to myuser;

create index idx_keywords_itemid
    on keywords (itemid);

create index idx_keywords_language
    on keywords (upper(language::text));

create index idx_keywords_keyword_trgm
    on keywords using gin (keyword gin_trgm_ops);

create table collection_titles
(
    collectionid integer,
    language     varchar,
    title        varchar
);

alter table collection_titles
    owner to myuser;

create table affiliations
(
    author        integer,
    num           integer,
    language      varchar,
    affiliationid integer,
    name          varchar,
    country       varchar,
    town          varchar,
    address       varchar
);

alter table affiliations
    owner to myuser;

create index idx_affiliations_author
    on affiliations (author);

create index idx_affiliations_num
    on affiliations (num);

create index idx_affiliations_affiliationid
    on affiliations (affiliationid);

create index idx_affiliations_language_upper
    on affiliations (upper(language::text));

create index idx_affiliations_name_trgm
    on affiliations using gin (name gin_trgm_ops);

create index idx_affiliations_country_trgm
    on affiliations using gin (country gin_trgm_ops);

create index idx_affiliations_town_trgm
    on affiliations using gin (town gin_trgm_ops);

create index idx_affiliations_address_trgm
    on affiliations using gin (address gin_trgm_ops);

create table journal_vak_data
(
    number                integer,
    issn                  varchar,
    title                 varchar,
    scientificspecialties varchar,
    inclusiondate         varchar,
    category              varchar,
    date_start            date,
    date_end              date
);

alter table journal_vak_data
    owner to myuser;

create table users
(
    id            serial
        primary key,
    username      text not null
        unique,
    password_hash text not null,
    avatar        bytea,
    signature     text,
    name          text
);

alter table users
    owner to myuser;

create materialized view author_citations_view as
SELECT DISTINCT a.authorid                                          AS author_id,
                (c.lastname::text || ' '::text) || c.initials::text AS author_name,
                b.authorid                                          AS citing_author,
                (b.lastname::text || ' '::text) || b.initials::text AS citing_author_name,
                a.author_item_id,
                d.title                                             AS author_item_title,
                a.citing_id                                         AS citing,
                e.title                                             AS citing_item_title
FROM (SELECT citing_data.authorid,
             citing_data.citingpublication,
             citing_data.authorpublication,
             (regexp_matches(citing_data.citingpublication::text, '\\?id=([0-9]+)$'::text))[1]::bigint AS citing_id,
             (regexp_matches(citing_data.authorpublication::text, '\\?id=([0-9]+)$'::text))[1]::bigint AS author_item_id
      FROM new_data.citing_data
      WHERE citing_data.citingpublication::text ~ '\\?id=[0-9]+$'::text
        AND citing_data.authorpublication::text ~ '\\?id=[0-9]+$'::text) a
         JOIN new_data.authors b ON b.itemid = a.citing_id
         JOIN new_data.authors c ON c.itemid = a.author_item_id AND c.authorid = a.authorid
         JOIN new_data.items d ON d.itemid = a.author_item_id
         JOIN new_data.items e ON e.itemid = a.citing_id
WHERE b.authorid IS NOT NULL
  AND a.authorid IS NOT NULL;

alter materialized view author_citations_view owner to myuser;

create materialized view author_journal_vak as
SELECT DISTINCT a.authorid,
                (a.lastname::text || ' '::text) || a.initials::text AS author_name,
                i.itemid,
                i.title,
                j.issn,
                j.name                                              AS journal_name,
                v.category,
                v.scientificspecialties,
                v.date_start,
                v.date_end
FROM new_data.authors a
         LEFT JOIN new_data.items i ON i.itemid = a.itemid
         LEFT JOIN new_data.journals j ON i.itemid = j.itemid
         LEFT JOIN new_data.journal_vak_data v ON v.issn::text = j.issn::text
WHERE v.issn IS NOT NULL
  AND a.authorid IS NOT NULL;

alter materialized view author_journal_vak owner to myuser;

create index idx_author_journal_vak_authorid
    on author_journal_vak (authorid);

create materialized view authors_names_with_priority_view as
SELECT DISTINCT authorid                                                 AS value,
                initcap((COALESCE(lastname, ''::character varying)::text || ' '::text) ||
                        COALESCE(initials, ''::character varying)::text) AS name,
                CASE
                    WHEN language::text = 'RU'::text THEN 0
                    WHEN language::text = 'EN'::text THEN 1
                    ELSE 2
                    END                                                  AS lang_priority,
                length((COALESCE(lastname, ''::character varying)::text || ' '::text) ||
                       COALESCE(initials, ''::character varying)::text)  AS name_length
FROM new_data.authors
ORDER BY authorid,
         (
             CASE
                 WHEN language::text = 'RU'::text THEN 0
                 WHEN language::text = 'EN'::text THEN 1
                 ELSE 2
                 END),
         (length((COALESCE(lastname, ''::character varying)::text || ' '::text) ||
                 COALESCE(initials, ''::character varying)::text)) DESC;

alter materialized view authors_names_with_priority_view owner to myuser;

create index idx_authors_unique_name
    on authors_names_with_priority_view using gin (name gin_trgm_ops);

create materialized view popular_keywords_mv as
SELECT keyword,
       count(DISTINCT itemid) AS publications_count
FROM new_data.keywords
WHERE keyword IS NOT NULL
GROUP BY keyword;

alter materialized view popular_keywords_mv owner to myuser;

create index idx_popular_keywords_mv_publications
    on popular_keywords_mv (publications_count);

create materialized view journals_reference_mv as
SELECT DISTINCT issn,
                journal_name
FROM new_data.author_journal_vak
WHERE issn IS NOT NULL
  AND journal_name IS NOT NULL;

alter materialized view journals_reference_mv owner to myuser;

create materialized view vak_statistics_mv as
SELECT authorid,
       issn,
       date_start,
       date_end,
       scientificspecialties,
       category,
       itemid
FROM new_data.author_journal_vak
WHERE category::text = ANY (ARRAY ['К1'::character varying, 'К2'::character varying, 'К3'::character varying]::text[]);

alter materialized view vak_statistics_mv owner to myuser;

create index idx_vak_stats_mv_authorid
    on vak_statistics_mv (authorid);

create index idx_vak_stats_mv_dates
    on vak_statistics_mv (date_start, date_end);

create index idx_vak_stats_mv_issn
    on vak_statistics_mv (issn);

create materialized view all_keywords_mv as
SELECT lower(TRIM(BOTH FROM keyword)) AS keyword,
       count(DISTINCT itemid)         AS articles_count
FROM new_data.keywords
WHERE keyword IS NOT NULL
GROUP BY (lower(TRIM(BOTH FROM keyword)));

alter materialized view all_keywords_mv owner to myuser;

create index idx_all_keywords_mv_keyword
    on all_keywords_mv (keyword);

create materialized view keyword_year_stats_mv as
SELECT lower(TRIM(BOTH FROM k.keyword)) AS keyword,
       upper(k.language::text)          AS language,
       i.year,
       count(*)                         AS count
FROM new_data.keywords k
         JOIN new_data.items i ON i.itemid = k.itemid
WHERE k.keyword IS NOT NULL
  AND i.year IS NOT NULL
GROUP BY (lower(TRIM(BOTH FROM k.keyword))), (upper(k.language::text)), i.year;

alter materialized view keyword_year_stats_mv owner to myuser;

create index idx_keyword_year_stats_mv_year
    on keyword_year_stats_mv (year);

create index idx_keyword_year_stats_mv_language
    on keyword_year_stats_mv (language);

create index idx_keyword_year_stats_mv_keyword_trgm
    on keyword_year_stats_mv using gin (keyword gin_trgm_ops);

create index idx_keyword_year_stats_mv_combo
    on keyword_year_stats_mv (year, language, keyword);

create materialized view ref_typecode_mv as
SELECT DISTINCT typecode
FROM new_data.items
WHERE typecode IS NOT NULL;

alter materialized view ref_typecode_mv owner to myuser;

create materialized view ref_genreid_mv as
SELECT DISTINCT genreid
FROM new_data.items
WHERE genreid IS NOT NULL;

alter materialized view ref_genreid_mv owner to myuser;

create materialized view ref_language_mv as
SELECT DISTINCT authors.language
FROM new_data.authors
WHERE authors.language IS NOT NULL
UNION
SELECT DISTINCT items.language
FROM new_data.items
WHERE items.language IS NOT NULL;

alter materialized view ref_language_mv owner to myuser;

create materialized view ref_status_mv as
SELECT DISTINCT status
FROM new_data.authors
WHERE status IS NOT NULL;

alter materialized view ref_status_mv owner to myuser;

create materialized view ref_affiliation_countries_mv as
SELECT DISTINCT country
FROM new_data.affiliations
WHERE country IS NOT NULL;

alter materialized view ref_affiliation_countries_mv owner to myuser;

create materialized view ref_towns_mv as
SELECT DISTINCT town
FROM new_data.affiliations
WHERE town IS NOT NULL;

alter materialized view ref_towns_mv owner to myuser;

create materialized view ref_org_countries_mv as
SELECT DISTINCT countryid
FROM new_data.elibrary_organizations
WHERE countryid IS NOT NULL;

alter materialized view ref_org_countries_mv owner to myuser;

create materialized view authors_by_city_full_mv as
SELECT lower(TRIM(BOTH FROM af.town)) AS normalized_city,
       a.authorid,
       max(a.lastname::text)          AS lastname,
       max(a.initials::text)          AS initials,
       count(DISTINCT a.itemid)       AS publication_count
FROM new_data.authors a
         JOIN new_data.affiliations af ON a.id = af.author
WHERE af.town IS NOT NULL
GROUP BY (lower(TRIM(BOTH FROM af.town))), a.authorid;

alter materialized view authors_by_city_full_mv owner to myuser;

create index idx_authors_by_city_mv_city
    on authors_by_city_full_mv (normalized_city);

create index idx_authors_by_city_mv_city_count
    on authors_by_city_full_mv (normalized_city asc, publication_count desc);

create materialized view authors_by_city_mv as
SELECT lower(TRIM(BOTH FROM a.town)) AS normalized_city,
       count(DISTINCT au.authorid)   AS authors_count,
       count(DISTINCT au.itemid)     AS publications_count
FROM new_data.affiliations a
         JOIN new_data.authors au ON a.author = au.id
WHERE a.town IS NOT NULL
GROUP BY (lower(TRIM(BOTH FROM a.town)));

alter materialized view authors_by_city_mv owner to myuser;

create materialized view city_publications_mv as
SELECT lower(TRIM(BOTH FROM af.town)) AS original_city,
       a.itemid
FROM new_data.affiliations af
         JOIN new_data.authors a ON af.author = a.id
         JOIN new_data.keywords k ON k.itemid = a.itemid
WHERE af.town IS NOT NULL
GROUP BY (lower(TRIM(BOTH FROM af.town))), a.itemid;

alter materialized view city_publications_mv owner to myuser;

create index idx_city_publications_mv_city
    on city_publications_mv (original_city);

create index idx_city_publications_mv_itemid
    on city_publications_mv (itemid);

create materialized view city_organization_items_mv as
SELECT lower(TRIM(BOTH FROM af.town)) AS normalized_city,
       org.organizationname,
       a.itemid
FROM new_data.elibrary_organizations org
         JOIN new_data.affiliations af ON org.organizationid = af.affiliationid
         JOIN new_data.authors a ON a.id = af.author
WHERE af.town IS NOT NULL
  AND org.organizationname IS NOT NULL
GROUP BY (lower(TRIM(BOTH FROM af.town))), org.organizationname, a.itemid;

alter materialized view city_organization_items_mv owner to myuser;

create materialized view organization_keyword_items_mv as
SELECT e.organizationid,
       e.organizationname,
       a.lastname::text || a.initials::text AS author,
       a.itemid,
       k.keyword
FROM new_data.elibrary_organizations e
         JOIN new_data.affiliations af ON af.affiliationid = e.organizationid
         JOIN new_data.authors a ON a.id = af.author
         JOIN new_data.keywords k ON k.itemid = a.itemid;

alter materialized view organization_keyword_items_mv owner to myuser;

create index idx_org_kw_mv_keyword
    on organization_keyword_items_mv (keyword);

create index idx_org_kw_mv_orgid
    on organization_keyword_items_mv (organizationid);

create index idx_org_kw_mv_itemid
    on organization_keyword_items_mv (itemid);

create materialized view authors_items_view as
SELECT a.authorid,
       i.itemid,
       i.title,
       i.year,
       j.name AS journal,
       i.link,
       aff.affiliationid,
       aff.town,
       k.keyword
FROM new_data.authors a
         JOIN new_data.items i ON a.itemid = i.itemid
         LEFT JOIN new_data.journals j ON i.itemid = j.itemid
         LEFT JOIN new_data.affiliations aff ON a.id = aff.author
         LEFT JOIN new_data.keywords k ON a.itemid = k.itemid;

alter materialized view authors_items_view owner to myuser;

create index authors_items_view_authorid_idx
    on authors_items_view (authorid);

create index authors_items_view_affiliationid_idx
    on authors_items_view (affiliationid);

create index authors_items_view_town_idx
    on authors_items_view (town);

create index authors_items_view_keyword_idx
    on authors_items_view (keyword);

create index authors_items_view_year_idx
    on authors_items_view (year);

create materialized view popular_organizations_mv as
SELECT TRIM(BOTH FROM e.organizationname) AS organization,
       e.organizationid                   AS id,
       count(DISTINCT a.itemid)           AS publications_count
FROM new_data.elibrary_organizations e
         JOIN new_data.affiliations af ON e.organizationid = af.affiliationid
         JOIN new_data.authors a ON af.author = a.id
WHERE e.organizationname IS NOT NULL
GROUP BY (TRIM(BOTH FROM e.organizationname)), e.organizationid;

alter materialized view popular_organizations_mv owner to myuser;

create materialized view publications_by_year_mv as
SELECT year,
       sum(publications_count) AS publications_count
FROM (SELECT items.year,
             count(*) AS publications_count
      FROM new_data.items
      WHERE items.year IS NOT NULL
      GROUP BY items.year
      UNION ALL
      SELECT 2023,
             9876
      UNION ALL
      SELECT 2024,
             12004
      UNION ALL
      SELECT 2025,
             9087) union_data
GROUP BY year;

alter materialized view publications_by_year_mv owner to myuser;

create function set_limit(real) returns real
    strict
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function set_limit(real) owner to postgres;

create function show_limit() returns real
    stable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function show_limit() owner to postgres;

create function show_trgm(text) returns text[]
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function show_trgm(text) owner to postgres;

create function similarity(text, text) returns real
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function similarity(text, text) owner to postgres;

create function similarity_op(text, text) returns boolean
    stable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function similarity_op(text, text) owner to postgres;

create function word_similarity(text, text) returns real
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function word_similarity(text, text) owner to postgres;

create function word_similarity_op(text, text) returns boolean
    stable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function word_similarity_op(text, text) owner to postgres;

create function word_similarity_commutator_op(text, text) returns boolean
    stable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function word_similarity_commutator_op(text, text) owner to postgres;

create function similarity_dist(text, text) returns real
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function similarity_dist(text, text) owner to postgres;

create function word_similarity_dist_op(text, text) returns real
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function word_similarity_dist_op(text, text) owner to postgres;

create function word_similarity_dist_commutator_op(text, text) returns real
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function word_similarity_dist_commutator_op(text, text) owner to postgres;

create function gtrgm_in(cstring) returns new_data.gtrgm
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_in(cstring) owner to postgres;

create function gtrgm_out(new_data.gtrgm) returns cstring
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_out(new_data.gtrgm) owner to postgres;

create function gtrgm_consistent(internal, text, smallint, oid, internal) returns boolean
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_consistent(internal, text, smallint, oid, internal) owner to postgres;

create function gtrgm_distance(internal, text, smallint, oid, internal) returns double precision
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_distance(internal, text, smallint, oid, internal) owner to postgres;

create function gtrgm_compress(internal) returns internal
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_compress(internal) owner to postgres;

create function gtrgm_decompress(internal) returns internal
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_decompress(internal) owner to postgres;

create function gtrgm_penalty(internal, internal, internal) returns internal
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_penalty(internal, internal, internal) owner to postgres;

create function gtrgm_picksplit(internal, internal) returns internal
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_picksplit(internal, internal) owner to postgres;

create function gtrgm_union(internal, internal) returns new_data.gtrgm
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_union(internal, internal) owner to postgres;

create function gtrgm_same(new_data.gtrgm, new_data.gtrgm, internal) returns internal
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_same(new_data.gtrgm, new_data.gtrgm, internal) owner to postgres;

create function gin_extract_value_trgm(text, internal) returns internal
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gin_extract_value_trgm(text, internal) owner to postgres;

create function gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal) returns internal
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal) owner to postgres;

create function gin_trgm_consistent(internal, smallint, text, integer, internal, internal, internal, internal) returns boolean
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gin_trgm_consistent(internal, smallint, text, integer, internal, internal, internal, internal) owner to postgres;

create function gin_trgm_triconsistent(internal, smallint, text, integer, internal, internal, internal) returns "char"
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gin_trgm_triconsistent(internal, smallint, text, integer, internal, internal, internal) owner to postgres;

create function strict_word_similarity(text, text) returns real
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function strict_word_similarity(text, text) owner to postgres;

create function strict_word_similarity_op(text, text) returns boolean
    stable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function strict_word_similarity_op(text, text) owner to postgres;

create function strict_word_similarity_commutator_op(text, text) returns boolean
    stable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function strict_word_similarity_commutator_op(text, text) owner to postgres;

create function strict_word_similarity_dist_op(text, text) returns real
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function strict_word_similarity_dist_op(text, text) owner to postgres;

create function strict_word_similarity_dist_commutator_op(text, text) returns real
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function strict_word_similarity_dist_commutator_op(text, text) owner to postgres;

create function gtrgm_options(internal) returns void
    immutable
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gtrgm_options(internal) owner to postgres;

create function get_unique_sorted_names(names text[], sorting_keys integer[]) returns text[]
    immutable
    language plpgsql
as
$$
DECLARE
    result TEXT[];
BEGIN
    -- Проверка на одинаковую длину массивов
    IF array_length(names, 1) != array_length(sorting_keys, 1) THEN
        RAISE EXCEPTION 'Массивы names и sorting_keys должны иметь одинаковую длину';
    END IF;

    -- Собираем уникальные значения с максимальным приоритетом
    WITH paired_data AS (SELECT DISTINCT ON (name) -- Оставляем только уникальные имена
                                                   name,
                                                   sorting_key
                         FROM (SELECT unnest(names)           AS name,
                                      unnest(sorting_keys) AS sorting_key) AS raw_data
                         ORDER BY name, sorting_key
    )
    SELECT array_agg(name ORDER BY sorting_key)
    INTO result
    FROM paired_data;

    RETURN result;
END;
$$;

alter function get_unique_sorted_names(text[], integer[]) owner to myuser;

create function digest(text, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function digest(text, text) owner to postgres;

create function digest(bytea, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function digest(bytea, text) owner to postgres;

create function hmac(text, text, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function hmac(text, text, text) owner to postgres;

create function hmac(bytea, bytea, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function hmac(bytea, bytea, text) owner to postgres;

create function crypt(text, text) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function crypt(text, text) owner to postgres;

create function gen_salt(text) returns text
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gen_salt(text) owner to postgres;

create function gen_salt(text, integer) returns text
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gen_salt(text, integer) owner to postgres;

create function encrypt(bytea, bytea, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function encrypt(bytea, bytea, text) owner to postgres;

create function decrypt(bytea, bytea, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function decrypt(bytea, bytea, text) owner to postgres;

create function encrypt_iv(bytea, bytea, bytea, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function encrypt_iv(bytea, bytea, bytea, text) owner to postgres;

create function decrypt_iv(bytea, bytea, bytea, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function decrypt_iv(bytea, bytea, bytea, text) owner to postgres;

create function gen_random_bytes(integer) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gen_random_bytes(integer) owner to postgres;

create function gen_random_uuid() returns uuid
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function gen_random_uuid() owner to postgres;

create function pgp_sym_encrypt(text, text) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_sym_encrypt(text, text) owner to postgres;

create function pgp_sym_encrypt_bytea(bytea, text) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_sym_encrypt_bytea(bytea, text) owner to postgres;

create function pgp_sym_encrypt(text, text, text) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_sym_encrypt(text, text, text) owner to postgres;

create function pgp_sym_encrypt_bytea(bytea, text, text) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_sym_encrypt_bytea(bytea, text, text) owner to postgres;

create function pgp_sym_decrypt(bytea, text) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_sym_decrypt(bytea, text) owner to postgres;

create function pgp_sym_decrypt_bytea(bytea, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_sym_decrypt_bytea(bytea, text) owner to postgres;

create function pgp_sym_decrypt(bytea, text, text) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_sym_decrypt(bytea, text, text) owner to postgres;

create function pgp_sym_decrypt_bytea(bytea, text, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_sym_decrypt_bytea(bytea, text, text) owner to postgres;

create function pgp_pub_encrypt(text, bytea) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_encrypt(text, bytea) owner to postgres;

create function pgp_pub_encrypt_bytea(bytea, bytea) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_encrypt_bytea(bytea, bytea) owner to postgres;

create function pgp_pub_encrypt(text, bytea, text) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_encrypt(text, bytea, text) owner to postgres;

create function pgp_pub_encrypt_bytea(bytea, bytea, text) returns bytea
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_encrypt_bytea(bytea, bytea, text) owner to postgres;

create function pgp_pub_decrypt(bytea, bytea) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_decrypt(bytea, bytea) owner to postgres;

create function pgp_pub_decrypt_bytea(bytea, bytea) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_decrypt_bytea(bytea, bytea) owner to postgres;

create function pgp_pub_decrypt(bytea, bytea, text) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_decrypt(bytea, bytea, text) owner to postgres;

create function pgp_pub_decrypt_bytea(bytea, bytea, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_decrypt_bytea(bytea, bytea, text) owner to postgres;

create function pgp_pub_decrypt(bytea, bytea, text, text) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_decrypt(bytea, bytea, text, text) owner to postgres;

create function pgp_pub_decrypt_bytea(bytea, bytea, text, text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_pub_decrypt_bytea(bytea, bytea, text, text) owner to postgres;

create function pgp_key_id(bytea) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function pgp_key_id(bytea) owner to postgres;

create function armor(bytea) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function armor(bytea) owner to postgres;

create function armor(bytea, text[], text[]) returns text
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function armor(bytea, text[], text[]) owner to postgres;

create function dearmor(text) returns bytea
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;
$$;

alter function dearmor(text) owner to postgres;

create function pgp_armor_headers(text, out key text, out value text) returns setof setof record
    immutable
    strict
    parallel safe
    language c
as
$$
begin
-- missing source code
end;

$$;

alter function pgp_armor_headers(text, out text, out text) owner to postgres;

create operator % (procedure = similarity_op, leftarg = text, rightarg = text, commutator = %, join = pg_catalog.matchingjoinsel, restrict = pg_catalog.matchingsel);

alter operator %(text, text) owner to postgres;

create operator <-> (procedure = similarity_dist, leftarg = text, rightarg = text, commutator = <->);

alter operator <->(text, text) owner to postgres;

create operator family gist_trgm_ops using gist;

alter operator family gist_trgm_ops using gist add
    operator 1 %(text, text),
    operator 2 <->(text, text) for order by float_ops,
    operator 3 pg_catalog.~~(text, text),
    operator 4 pg_catalog.~~*(text, text),
    operator 5 pg_catalog.~(text, text),
    operator 6 pg_catalog.~*(text, text),
    operator 7 %>(text, text),
    operator 8 <->>(text, text) for order by float_ops,
    operator 9 %>>(text, text),
    operator 10 <->>>(text, text) for order by float_ops,
    operator 11 pg_catalog.=(text, text),
    function 6(text, text) gtrgm_picksplit(internal, internal),
    function 7(text, text) gtrgm_same(new_data.gtrgm, new_data.gtrgm, internal),
    function 8(text, text) gtrgm_distance(internal, text, smallint, oid, internal),
    function 10(text, text) gtrgm_options(internal),
    function 2(text, text) gtrgm_union(internal, internal),
    function 3(text, text) gtrgm_compress(internal),
    function 4(text, text) gtrgm_decompress(internal),
    function 5(text, text) gtrgm_penalty(internal, internal, internal),
    function 1(text, text) gtrgm_consistent(internal, text, smallint, oid, internal);

alter operator family gist_trgm_ops using gist owner to postgres;

create operator class gist_trgm_ops for type text using gist as storage new_data.gtrgm function 6(text, text) gtrgm_picksplit(internal, internal),
	function 1(text, text) gtrgm_consistent(internal, text, smallint, oid, internal),
	function 7(text, text) gtrgm_same(new_data.gtrgm, new_data.gtrgm, internal),
	function 5(text, text) gtrgm_penalty(internal, internal, internal),
	function 2(text, text) gtrgm_union(internal, internal);

alter operator class gist_trgm_ops using gist owner to postgres;

create operator family gin_trgm_ops using gin;

alter operator family gin_trgm_ops using gin add
    operator 6 pg_catalog.~*(text, text),
    operator 7 %>(text, text),
    operator 11 pg_catalog.=(text, text),
    operator 9 %>>(text, text),
    operator 1 %(text, text),
    operator 3 pg_catalog.~~(text, text),
    operator 4 pg_catalog.~~*(text, text),
    operator 5 pg_catalog.~(text, text),
    function 1(text, text) pg_catalog.btint4cmp(integer, integer),
    function 4(text, text) gin_trgm_consistent(internal, smallint, text, integer, internal, internal, internal, internal),
    function 6(text, text) gin_trgm_triconsistent(internal, smallint, text, integer, internal, internal, internal),
    function 2(text, text) gin_extract_value_trgm(text, internal),
    function 3(text, text) gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal);

alter operator family gin_trgm_ops using gin owner to postgres;

create operator class gin_trgm_ops for type text using gin as storage integer function 3(text, text) gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal),
	function 2(text, text) gin_extract_value_trgm(text, internal);

alter operator class gin_trgm_ops using gin owner to postgres;

-- Cyclic dependencies found

create operator %> (procedure = word_similarity_commutator_op, leftarg = text, rightarg = text, commutator = <%, join = pg_catalog.matchingjoinsel, restrict = pg_catalog.matchingsel);

alter operator %>(text, text) owner to postgres;

create operator <% (procedure = word_similarity_op, leftarg = text, rightarg = text, commutator = %>, join = pg_catalog.matchingjoinsel, restrict = pg_catalog.matchingsel);

alter operator <%(text, text) owner to postgres;

-- Cyclic dependencies found

create operator %>> (procedure = strict_word_similarity_commutator_op, leftarg = text, rightarg = text, commutator = <<%, join = pg_catalog.matchingjoinsel, restrict = pg_catalog.matchingsel);

alter operator %>>(text, text) owner to postgres;

create operator <<% (procedure = strict_word_similarity_op, leftarg = text, rightarg = text, commutator = %>>, join = pg_catalog.matchingjoinsel, restrict = pg_catalog.matchingsel);

alter operator <<%(text, text) owner to postgres;

-- Cyclic dependencies found

create operator <->> (procedure = word_similarity_dist_commutator_op, leftarg = text, rightarg = text, commutator = <<->);

alter operator <->>(text, text) owner to postgres;

create operator <<-> (procedure = word_similarity_dist_op, leftarg = text, rightarg = text, commutator = <->>);

alter operator <<->(text, text) owner to postgres;

-- Cyclic dependencies found

create operator <->>> (procedure = strict_word_similarity_dist_commutator_op, leftarg = text, rightarg = text, commutator = <<<->);

alter operator <->>>(text, text) owner to postgres;

create operator <<<-> (procedure = strict_word_similarity_dist_op, leftarg = text, rightarg = text, commutator = <->>>);

alter operator <<<->(text, text) owner to postgres;


