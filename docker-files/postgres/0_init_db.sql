create table if not exists dataset
(
    id                   serial
        constraint dataset_pk
            primary key,
    job_id             varchar,
    is_example          boolean,
    dataset_name varchar,
    email                varchar,
    did_send_mail        boolean,
    status               varchar,
    expiration_date     date,
    creation_date_time   date,
    token                varchar,
    matrix               json,
    config_json        json,
    json_key            varchar
);

create index if not exists dataset_job_id_index
    on dataset (job_id);

create table if not exists optimization_result
(
    dataset_id        integer not null
        constraint optimization_result_dataset_id_fk
            references dataset
            on delete cascade,
    strategy          varchar not null,
    layout_number     integer not null,
    optimization_step integer not null,
    rects             json,
    intersections     json,
    stats             json,
    element_groups    json,
    constraint optimization_result_pk
        primary key (dataset_id, strategy, layout_number, optimization_step)
);
