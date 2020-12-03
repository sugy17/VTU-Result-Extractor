def get_default_marks(code, name, sem):
    default_marks = {
        # type : (MinExt,MinTotal,MaxTotal,Credits),
        'lab': (19, 40, 100, 2),
        'theory': (19, 40, 100, 4),
        'elective': (19, 40, 100, 3),
        'project-7': (33, 33, 100, 2),
        'project-8': (19, 40, 100, 8),
        'internship': (19, 40, 100, 3),
        'seminar': (33, 33, 100, 1),
        'MATDIP': (19, 40, 100, 0),
        'light': (9, 20, 50, 4)
    }

    default_depts = {'CS', 'EC', 'TE', 'ME', 'CV', 'IS'}

    key = 'theory'
    if code[2:4] in default_depts:  # change later
        if len(code) == 8:
            key = 'elective'
        elif len(code) == 7:
            # 2 lettered dept
            if (code[4] == 'L') and ('lab' in name.lower()):
                key = 'lab'
            elif (code[4] == 'P') and ('project' in name.lower()):
                key = 'project-' + sem
            elif (code[4] == 'I') and ('intern' in name.lower()):
                key = 'internship'
            elif (code[4] == 'S') and ('seminar' in name.lower()):
                key = 'seminar'
            elif code[4].isdigit():
                key = 'elective'
    elif 'DIP' in code:
        key = 'MATDIP'
    else:
        if len(code) == 8:
            # 3 lettered dept
            if (code[5] == 'L') and ('lab' in name.lower()):
                key = 'lab'
            elif (code[5] == 'P') and ('project' in name.lower()):
                key = 'project-' + sem
            elif (code[5] == 'I') and ('intern' in name.lower()):
                key = 'internship'
            elif (code[5] == 'S') and ('seminar' in name.lower()):
                key = 'seminar'
            elif code[5].isdigit():
                key = 'elective'
        elif len(code) == 7:
            # 2 lettered dept
            if (code[4] == 'L') and ('lab' in name.lower()):
                key = 'lab'
            elif (code[4] == 'P') and ('project' in name.lower()):
                key = 'project-' + sem
            elif (code[4] == 'I') and ('intern' in name.lower()):
                key = 'internship'
            elif (code[4] == 'S') and ('seminar' in name.lower()):
                key = 'seminar'
            elif code[4].isdigit():
                key = 'elective'
        else:
            key = 'elective'
    #     # 3 lettered dept
    #     else:
    #         key = 'theory'
    # elif len(code) == 6:
    #     # 2 lettered dept
    #     key = 'theory'
    # else:
    #     # raise execption
    #     pass
    return default_marks[key][0], default_marks[key][1], default_marks[key][2], default_marks[key][3]
