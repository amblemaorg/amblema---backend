# app/helpers/peca_yearbook_helper.py

def update_yearbook_data_in_approval(peca):
    """
    Update the diagnostic summary and sections (including student names) 
    in the most recent approved or pending yearbook request.
    This ensures that the Yearbook PDF always shows synchronized data.
    """
    from app.models.request_content_approval_model import RequestContentApproval
    
    # 1.0 Ensure minimal data is loaded (might be excluded in the initial query)
    # We check if these fields are None or haven't been loaded.
    if peca.project is None or peca.school is None or peca.yearbook is None:
        from app.models.peca_project_model import PecaProject
        fields_to_load = []
        if peca.project is None: fields_to_load.append('project')
        if peca.school is None: fields_to_load.append('school')
        if peca.yearbook is None: fields_to_load.append('yearbook')
        
        temp_peca = PecaProject.objects(id=peca.id).only(*fields_to_load).first()
        if temp_peca:
            if peca.project is None: peca.project = temp_peca.project
            if peca.school is None: peca.school = temp_peca.school
            if peca.yearbook is None: peca.yearbook = temp_peca.yearbook

    # 1.1 Find the PENDING yearbook request
    # Type 7 = Yearbook, Status 1 = Pending
    if not peca.project or not peca.project.id:
        return False
        
    pending_request = RequestContentApproval.objects(
        project__id=peca.project.id,
        type="7",
        status="1"
    ).order_by("-createdAt").first()



    # 2. Prepare new diagnostic summaries from current peca state
    new_summaries = {}
    for lapse_idx in [1, 2, 3]:
        lapse_key = 'lapse{}'.format(lapse_idx)
        summary_list = []
        for section in sorted(peca.school.sections.filter(isDeleted=False), key=lambda x: (x.grade, x.name)):
            s_diag = section.diagnostics[lapse_key]
            summary_list.append({
                'grade': section.grade,
                'name': section.name,
                'wordsPerMin': s_diag.wordsPerMin,
                'wordsPerMinIndex': float(s_diag.wordsPerMinIndex) if s_diag.wordsPerMinIndex is not None else 0,
                'wordsPerMinCount': s_diag.wordsPerMinCount,
                'multiplicationsPerMin': s_diag.multiplicationsPerMin,
                'multiplicationsPerMinIndex': float(s_diag.multiplicationsPerMinIndex) if s_diag.multiplicationsPerMinIndex is not None else 0,
                'multiplicationsPerMinCount': s_diag.multiplicationsPerMinCount,
                'operationsPerMin': s_diag.operationsPerMin,
                'operationsPerMinIndex': float(s_diag.operationsPerMinIndex) if s_diag.operationsPerMinIndex is not None else 0,
                'operationsPerMinCount': s_diag.operationsPerMinCount
            })
        new_summaries[lapse_key] = summary_list

    # 3. Prepare new sections array from current peca state (including student names)
    new_sections = []
    for section in peca.school.sections.filter(isDeleted=False):
        section_data = {
            'id': str(section.id),
            'name': section.name,
            'grade': section.grade,
            'image': section.image,
            'students': [
                {
                    'id': str(st.id),
                    'firstName': st.firstName,
                    'lastName': st.lastName,
                    'cardId': st.cardId,
                    'cardType': st.cardType,
                    'gender': st.gender,
                    'birthdate': st.birthdate.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if st.birthdate else None
                } for st in section.students.filter(isDeleted=False)
            ]
        }
        if section.teacher:
            section_data['teacher'] = {
                'id': str(section.teacher.id),
                'firstName': section.teacher.firstName,
                'lastName': section.teacher.lastName
            }
        new_sections.append(section_data)

    # 4. Update separate RequestContentApproval document (Only Pending)
    changed = False
    if pending_request:
        detail = pending_request.detail
        for lapse_key, summary in new_summaries.items():
            if lapse_key in detail:
                detail[lapse_key]['diagnosticSummary'] = summary
                changed = True
        if 'sections' in detail:
            detail['sections'] = new_sections
            changed = True
        
        if changed:
            pending_request.detail = detail
            pending_request.save(validate=False)

    # 5. Update embedded Approval in YearbookApproval collection
    # Only update the pending ones and the single MOST RECENT approved one.
    from app.models.yearbook_approval_model import YearbookApproval
    sync_embedded = False
    found_approved = False
    
    approvals = YearbookApproval.objects(pecaId=str(peca.id)).order_by('-createdAt')
    
    for yearbook_approval in approvals:
        approval = yearbook_approval.approval
        is_pending = approval.status == "1"
        is_approved = approval.status == "2"
        
        if is_approved and found_approved:
            # We already updated the most recent approved, so skip older ones
            continue
            
        if is_pending or is_approved:
            app_detail = approval.detail
            for lapse_key, summary in new_summaries.items():
                if lapse_key in app_detail:
                    app_detail[lapse_key]['diagnosticSummary'] = summary
            if 'sections' in app_detail:
                app_detail['sections'] = new_sections
            approval.detail = app_detail
            yearbook_approval.save(validate=False)
            sync_embedded = True
            
            if is_approved:
                found_approved = True
    
    return sync_embedded
