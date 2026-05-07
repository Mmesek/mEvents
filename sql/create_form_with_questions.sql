DECLARE 

v_form_id int4;
v_question_id int4;
question jsonb;
opt TEXT;

BEGIN

INSERT INTO
    "Form" (title, description)
VALUES
    (title, description) RETURNING id INTO v_form_id;

FOR question IN
    SELECT
        *
    FROM
        jsonb_array_elements(questions)
    LOOP    
        INSERT INTO
            "Question" (type, title, description, min_length, max_length)
        VALUES
            (
                question ->> 'type',
                question ->> 'title',
                question ->> 'description',
                COALESCE((question ->> 'min_length') :: int, NULL),
                COALESCE((question ->> 'max_length') :: int, NULL)
            ) RETURNING id INTO v_question_id;
    
        -- 2c. Insert Options if they exist
        IF question ? 'options' THEN 
            FOR opt IN
                SELECT
                    *
                FROM
                    jsonb_array_elements(question -> 'options') LOOP
                INSERT INTO
                    "Question_Options" (question_id, value)
                VALUES
                    (v_question_id, opt);
            END LOOP;
        END IF;
    
    -- 2d. Link Question to Form
    INSERT INTO
        "Form_Questions" (form_id, question_id, required, "order")
    VALUES
        (
            v_form_id,
            v_question_id,
            COALESCE((question ->> 'required') :: boolean, false),
            COALESCE((question ->> 'order') :: int4, 0)
        );
    
END LOOP;

RETURN jsonb_build_object(
    'form_id',
    v_form_id,
    'status',
    'created',
    'message',
    'Form and questions inserted successfully'
);

END;