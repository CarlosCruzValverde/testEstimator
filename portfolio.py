from flask import Blueprint
from datetime import datetime
from flask import flash
from flask import redirect
from flask import render_template
from flask import session, abort
from flask import url_for
from flask import jsonify
from auth import login_required
from flask import Flask, request, jsonify
from sqlalchemy.orm import joinedload
from flask import current_app
from models import CostEstimation, Project, EstimationEntry, MiscEquipmentEstimation, MiscEquipmentEntry, LaborCostEstimation, LaborCostEntry, ProjectSummary
from database import db


bp = Blueprint("portfolio", __name__)


@bp.route("/")
@login_required
def index():
    return render_template("portfolio/index.html")


@bp.route("/portfolio/new_project", methods=["GET", "POST"])
@login_required
def new_project():  
    if request.method == "POST":
        # Retrieve the JSON data from the request
        data = request.get_json()

        # Validate required fields
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = ['user_id', 'address', 'start_date', 'p_type']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Validate the user ID (ensure the user is authenticated)
        user_id = session["user_id"]  # Use the logged-in user's ID
        if not user_id or user_id != data['user_id']:  # Compare integers directly
            return jsonify({"error": "Not authenticated"}), 401

        # Parse the start date (ensure it's in the correct format)
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Create a new project
        new_project = Project(
            address=data['address'],
            company=data.get('company', 'Chargie'),  # Default to 'Chargie' if not provided
            start_date=start_date,
            p_type=data['p_type'],
            status="started",  # Default status
            created_at=datetime.utcnow(),
            user_id=user_id
        )

        # Save the project to the database
        db.session.add(new_project)
        db.session.commit()

        # Return the project ID to the frontend
        return jsonify({"project_id": new_project.id, "status": new_project.status}), 201
    
    # Handle GET request
    return render_template("portfolio/new_project.html", user_id=session["user_id"])


@bp.route("/portfolio/estimate_awg_cond", methods=["GET", "POST"])
@login_required
def estimate_awg_cond():
    if request.method == "POST":
        # Get the JSON data from the request
        data = request.get_json()

        # Validate the data
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Extract fields from the JSON data with defaults
        project_id = data.get('project_id')
        awg_data = data.get('awgData', [])  # Default to empty list
        conduit_data = data.get('conduitData', [])  # Default to empty list
        tax = data.get('tax', 0)  # Default to 0
        tax_amount = data.get('taxAmount', 0)  # Default to 0
        grand_total = data.get('grandTotal', 0)  # Default to 0
        awg_total = data.get('awgTotal', 0)  # Default to 0
        conduit_total = data.get('conduitTotal', 0)  # Default to 0
        notes_awg = data.get('notes_awg', '')  # Default to empty string
        notes_conduit = data.get('notes_conduit', '')  # Default to empty string

        # Validate required fields - project_id is the only truly required field
        if not project_id:
            return jsonify({'success': False, 'message': 'Project ID is required'}), 400

        # Validate that at least one section has data
        if not awg_data and not conduit_data:
            return jsonify({'success': False, 'message': 'At least one section (AWG or Conduit) must have data'}), 400

        # Validate data formats
        if not isinstance(awg_data, list) or not isinstance(conduit_data, list):
            return jsonify({'success': False, 'message': 'Invalid data format for AWG or Conduit'}), 400

        # Find the project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404

        try:
            # Create a new CostEstimation record
            cost_estimation = CostEstimation(
                tax_percentage=tax,
                tax_amount=tax_amount,
                grand_total=grand_total,
                awg_total=awg_total,
                conduit_total=conduit_total,
                created_at=datetime.utcnow(),
                project_id=project.id
            )
            db.session.add(cost_estimation)
            db.session.commit()

            # Save AWG entries if they exist
            for awg in awg_data:
                entry = EstimationEntry(
                    type="AWG",
                    name=awg.get('name', ''),
                    cost=awg.get('cost', 0),
                    length=awg.get('length', 0),
                    subtotal=awg.get('subtotal', 0),
                    notes_awg=notes_awg,
                    cost_estimation_id=cost_estimation.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(entry)

            # Save Conduit entries if they exist
            for conduit in conduit_data:
                entry = EstimationEntry(
                    type="Conduit",
                    name=conduit.get('name', ''),
                    cost=conduit.get('cost', 0),
                    length=conduit.get('length', 0),
                    subtotal=conduit.get('subtotal', 0),
                    notes_conduit=notes_conduit,
                    cost_estimation_id=cost_estimation.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(entry)

            # Update project status
            project.status = "wire_conduit_submitted"
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Wire & Conduit Estimation submitted',
                'status': project.status,
            }), 201

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting AWG/Conduit estimation: {str(e)}")
            return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

    # Handle GET request
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({'success': False, 'message': 'Project ID is required'}), 400

    project = Project.query.get(project_id)
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404

    return render_template("portfolio/estimate_awg_cond.html", project_id=project_id)


@bp.route("/portfolio/estimate_misc_equip", methods=["GET", "POST"])
@login_required
def estimate_misc_equip():
    if request.method == "POST":
        # Get the JSON data from the request
        data = request.get_json()

        # Validate the data
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Extract fields from the JSON data
        project_id = data.get('project_id')
        misc_data = data.get('miscData', [])  # Default to empty list
        equipment_data = data.get('equipmentData', [])  # Default to empty list
        tax = data.get('tax', 0)  # Default to 0
        tax_amount = data.get('taxAmount', 0)  # Default to 0
        grand_total = data.get('grandTotal', 0)  # Default to 0
        misc_total = data.get('miscTotal', 0)  # Default to 0
        equipment_total = data.get('equipmentTotal', 0)  # Default to 0
        notes_misc = data.get('notes_misc', '')  # Default to empty string
        notes_equip = data.get('notes_equip', '')  # Default to empty string

        # Validate required fields - project_id is the only truly required field
        if not project_id:
            return jsonify({'success': False, 'message': 'Project ID is required'}), 400

        # Validate that at least one section has data
        if not misc_data and not equipment_data:
            return jsonify({'success': False, 'message': 'At least one section (Miscellaneous or Equipment) must have data'}), 400

        # Validate data formats
        if not isinstance(misc_data, list) or not isinstance(equipment_data, list):
            return jsonify({'success': False, 'message': 'Invalid data format for Miscellaneous or Equipment'}), 400
        
        # Find the project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404

        try:    
            # Create a new MiscEquipmentEstimation record
            misc_equipment_estimation = MiscEquipmentEstimation(
                tax_percentage=tax,
                tax_amount=tax_amount,
                grand_total=grand_total,
                misc_total=misc_total,
                equipment_total=equipment_total,
                created_at=datetime.utcnow(),
                project_id=project.id
            )
            db.session.add(misc_equipment_estimation)
            db.session.commit()

            # Save Miscellaneous entries if they exist
            for misc in misc_data:
                entry = MiscEquipmentEntry(
                    type="Miscellaneous",
                    name=misc.get('name', ''),
                    cost=misc.get('cost', 0),
                    quantity=misc.get('quantity', 0),
                    subtotal=misc.get('subtotal', 0),
                    notes_misc=notes_misc,
                    misc_equipment_estimation_id=misc_equipment_estimation.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(entry)

            # Save Equipment entries if they exist
            for equip in equipment_data:
                entry = MiscEquipmentEntry(
                    type="Equipment",
                    name=equip.get('name', ''),
                    cost=equip.get('cost', 0),
                    quantity=equip.get('quantity', 0),
                    subtotal=equip.get('subtotal', 0),
                    notes_equip=notes_equip,
                    misc_equipment_estimation_id=misc_equipment_estimation.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(entry)

            # Update project status
            project.status = "misc_equipment_submitted"
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Miscellaneous & Equipment Estimation submitted',
                'status': project.status,
            }), 201

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting misc/equipment estimation: {str(e)}")
            return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
        
    # Handle GET request
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({'success': False, 'message': 'Project ID is required'}), 400

    project = Project.query.get(project_id)
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404

    return render_template("portfolio/estimate_misc_equip.html", project_id=project_id)


@bp.route("/portfolio/estimate_labor_cost", methods=["GET", "POST"])
@login_required
def estimate_labor_cost():
    if request.method == "POST":
        # Get the JSON data from the request
        data = request.get_json()

        # Validate the data
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Extract fields from the JSON data
        project_id = data.get('project_id')
        labor_data = data.get('laborData')
        low_voltage_data = data.get('lowVoltageData')
        labor_total = data.get('laborTotal')
        low_voltage_total = data.get('lowVoltageTotal')
        grand_total = data.get('grandTotal')

        # Validate required fields
        if not all([project_id, labor_data, low_voltage_data, labor_total, low_voltage_total, grand_total]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Validate Labor data
        if not isinstance(labor_data, list):
            return jsonify({'success': False, 'message': 'Invalid data format for Labor entries'}), 400
        
        # Find the project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404

        try:    
            # Create a new LaborCostEstimation record
            labor_cost_estimation = LaborCostEstimation(
                labor_total=labor_total,
                low_voltage_total=low_voltage_total,
                grand_total=grand_total,
                chargers_count=low_voltage_data.get('chargersCount'),
                charger_price=low_voltage_data.get('chargerPrice'),
                created_at=datetime.utcnow(),
                project_id=project.id
            )
            db.session.add(labor_cost_estimation)
            db.session.commit()

            # Save Labor entries
            for labor in labor_data:
                # Only save entries that have data
                if any([labor.get('rate'), labor.get('workers'), labor.get('hours'), labor.get('days')]):
                    entry = LaborCostEntry(
                        position=labor.get('position'),
                        rate=labor.get('rate'),
                        workers=labor.get('workers'),
                        hours=labor.get('hours'),
                        days=labor.get('days'),
                        subtotal=labor.get('subtotal'),
                        labor_cost_estimation_id=labor_cost_estimation.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(entry)

            # Update project status
            project.status = "labor_cost_submitted"
            # Commit all changes to the database
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Labor Cost Estimation submitted',
                'status': project.status,
            }), 201

        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            print(f"Error: {str(e)}")  # Log the error
            return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
        
    # Handle GET request
    # Get the project_id from the query parameters
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({'success': False, 'message': 'Project ID is required'}), 400

    # Fetch the project from the database
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404

    # Check if the project is in the correct status for this step
    if project.status not in ["misc_equipment_submitted", "labor_cost_submitted"]:
        return jsonify({
            'success': False, 
            'message': f'Project must be in misc_equipment_submitted status. Current status: {project.status}'
        }), 400

    return render_template("portfolio/estimate_labor_cost.html", project_id=project_id)


@bp.route("/portfolio/get_estimation_data")
@login_required
def get_estimation_data():
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({'success': False, 'message': 'Project ID required'}), 400
    
    #project = Project.query.get(project_id)
    
    # Get all estimation data for this project
    cost_estimation = CostEstimation.query.filter_by(project_id=project_id).first()
    misc_estimation = MiscEquipmentEstimation.query.filter_by(project_id=project_id).first()
    labor_estimation = LaborCostEstimation.query.filter_by(project_id=project_id).first()
    
    if not all([cost_estimation, misc_estimation, labor_estimation]):
        return jsonify({'success': False, 'message': 'Estimations not found'}), 404
    
    return jsonify({
        'success': True,
        'awg_total': cost_estimation.awg_total,
        'conduit_total': cost_estimation.conduit_total,
        'misc_total': misc_estimation.misc_total,
        'equipment_total': misc_estimation.equipment_total,
        'labor_total': labor_estimation.labor_total,
        'low_voltage_total': labor_estimation.low_voltage_total,
        'chargers_count': labor_estimation.chargers_count
    })


@bp.route("/portfolio/save_summary", methods=["GET", "POST"])
@login_required
def save_summary():
    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Validate required field
        if 'project_id' not in data:
            return jsonify({'success': False, 'message': 'Project ID is required'}), 400
        
        # Numeric validation for critical fields
        numeric_fields = [
            'awg_subtotal', 'conduit_subtotal', 'misc_subtotal', 'equipment_subtotal',
            'labor_subtotal', 'low_voltage_subtotal', 'permits_subtotal',
            'tax_subtotal', 'overhead_subtotal', 'grand_subtotal', 'grand_total', 'total_submitted', 'approved_amount'
        ]

        if not all(isinstance(data.get(field), (float, int)) for field in numeric_fields if field in data):
            return jsonify({
                'success': False,
                'message': 'Invalid numeric values detected',
                'details': {
                    field: data.get(field)
                    for field in numeric_fields
                    if field in data and not isinstance(data.get(field), (float, int))
                }
            }), 400
        
        # Find existing summary or create new one
        summary = ProjectSummary.query.filter_by(project_id=data['project_id']).first()
        if not summary:
            summary = ProjectSummary(project_id=data['project_id'])


        # List of all expected fields from your formData
        fields_to_update = [
            # AWG
            'awg_base_cost', 'awg_markup', 'awg_subtotal', 'awg_profit',
            # Conduit
            'conduit_base_cost', 'conduit_markup', 'conduit_subtotal', 'conduit_profit',
            # Miscellaneous
            'misc_base_cost', 'misc_markup', 'misc_subtotal', 'misc_profit',
            # Equipment
            'equipment_base_cost', 'equipment_markup', 'equipment_subtotal', 'equipment_profit',
            # Labor
            'labor_base_cost', 'labor_markup', 'labor_subtotal', 'labor_profit',
            # Low Voltage
            'low_voltage_base_cost', 'low_voltage_markup', 'low_voltage_subtotal', 'low_voltage_profit',
            # Permits
            'permits_base_cost', 'permits_markup', 'permits_subtotal', 'permits_profit',
            # Tax
            'tax_base_cost', 'tax_percentage', 'tax_subtotal',
            # Overhead
            'overhead_base_cost', 'overhead_percentage', 'overhead_subtotal',
            # Totals
            'grand_subtotal', 'grand_total',
            # Charger Info
            'price_per_charger',
            # Approval
            'approved',
            # Amount
            'total_submitted',
            'approved_amount',
            # Notes
            'notes'
        ]

        # Update all fields from form data
        for field in fields_to_update:
            if field in data:
                try:
                    # Convert to appropriate type
                    if field in ['approved']:
                        setattr(summary, field, int(data[field]) if data[field] is not None else None)
                    elif any(x in field for x in ['_cost', '_subtotal', '_profit', '_total', '_percentage']):
                        setattr(summary, field, float(data[field]))
                    else:
                        setattr(summary, field, data[field])
                except (ValueError, TypeError) as e:
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'message': f'Invalid value for {field}',
                        'field': field,
                        'value': data[field],
                        'error': str(e)
                    }), 400

        try:
            db.session.add(summary)
            # Update project status
            project = Project.query.get(data['project_id'])
            project.status = "completed"
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Summary saved successfully',
                'status': project.status,
            }), 201
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")  # Log the error
            return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
   
    # Handle GET request
    try:
        # Get the project_id from the query parameters
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'message': 'Project ID is required'}), 400

        # Fetch the project from the database
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404

        # Check if the project is in the correct status for this step
        if project.status not in ["labor_cost_submitted", "completed"]:
            return jsonify({
                'success': False, 
                'message': f'Project must be in completed status. Current status: {project.status}'
            }), 400
        
    except Exception as e:
        # Log the error here (configure your logging first)
        # current_app.logger.error(f"Error fetching estimate summary: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching the estimate summary',
            'error': str(e)
        }), 500

    return render_template("portfolio/estimate_summary.html", project_id=project_id)


@bp.route("/portfolio/projects")
@login_required
def projects():
    # Get all projects for the current user
    projects = Project.query.filter_by(user_id=session["user_id"]).order_by(Project.start_date.desc()).all()
    
    # Batch load all necessary related data
    project_ids = [p.id for p in projects]
    
    # Get most recent cost estimations
    latest_cost_estimations = get_latest_for_each_project(CostEstimation, project_ids)
    latest_misc_estimations = get_latest_for_each_project(MiscEquipmentEstimation, project_ids)
    latest_labor_estimations = get_latest_for_each_project(LaborCostEstimation, project_ids)

    # Get most recent project summaries
    latest_summaries = get_latest_for_each_project(ProjectSummary, project_ids)
    
    # Create mappings
    cost_map = {est.project_id: est for est in latest_cost_estimations}
    misc_map = {est.project_id: est for est in latest_misc_estimations}
    labor_map = {est.project_id: est for est in latest_labor_estimations}
    summary_map = {summary.project_id: summary for summary in latest_summaries}
    
    # Prepare project data
    project_list = []
    for project in projects:
        project_summary = summary_map.get(project.id)
        project_data = {
            'id': project.id,
            'address': project.address,
            'company': project.company,
            'start_date': project.start_date,
            'p_type': project.p_type,
            'status': project.status,
            'chargers_count': labor_map.get(project.id, {}).chargers_count if labor_map.get(project.id)
             else None,
            'approved': project_summary.approved if project_summary else None,
            'approved_amount': project_summary.approved_amount if project_summary else None,
            'total_submitted': project_summary.total_submitted if project_summary else None
        }
        project_list.append(project_data)
    
    return render_template("portfolio/listing_projects.html", projects=project_list)

def get_latest_for_each_project(model, project_ids):
    """Helper function to get most recent record for each project"""
    if not project_ids:
        return []
        
    subq = db.session.query(
        model.project_id,
        db.func.max(model.created_at).label('max_created_at')
    ).filter(
        model.project_id.in_(project_ids)
    ).group_by(
        model.project_id
    ).subquery()
    
    return db.session.query(model).join(
        subq,
        db.and_(
            model.project_id == subq.c.project_id,
            model.created_at == subq.c.max_created_at
        )
    ).all()


@bp.route("/project_review/<int:project_id>")
@login_required
def project_review(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        data = {
            'project': project,
            'cost_estimation': None,
            'misc_equipment': None,
            'labor_cost': None,
            'summary': None
        }

        # Handle Cost Estimation - Filter in Python
        cost_estimation = project.cost_estimations.first()
        if cost_estimation:
            data['cost_estimation'] = {
                'awg': [e for e in cost_estimation.entries if e.type == 'AWG'],
                'conduit': [e for e in cost_estimation.entries if e.type == 'Conduit'],
                'main': cost_estimation
            }

        # Handle Misc Equipment - Filter in Python
        misc_equipment = project.misc_equipment_estimations.first()
        if misc_equipment:
            data['misc_equipment'] = {
                'misc': [e for e in misc_equipment.entries if e.type == 'Miscellaneous'],
                'equipment': [e for e in misc_equipment.entries if e.type == 'Equipment'],
                'main': misc_equipment
            }

        # Handle Labor Cost
        labor_cost = project.labor_cost_estimations.first()
        if labor_cost:
            data['labor_cost'] = {
                'entries': labor_cost.entries,  # Already a list
                'main': labor_cost
            }

        # Handle Summary
        summary = project.summaries.first()
        data['summary'] = summary

        return render_template("portfolio/project_review.html", **data, project_id=project_id)

    except Exception as e:
        current_app.logger.error(f"Error loading project review: {str(e)}")
        abort(500)


@bp.route("/update_basic_info/<int:project_id>", methods=["POST"])
@login_required
def update_basic_info(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Update fields from form data
        project.address = request.form.get('address')
        project.company = request.form.get('company')
        project.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        project.p_type = request.form.get('p_type')
        
        db.session.commit()
        flash('Basic information updated successfully!', 'success')
        return redirect(url_for('portfolio.project_review', project_id=project_id))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating basic info: {str(e)}")
        flash('Error updating basic information', 'danger')
        return redirect(url_for('portfolio.project_review', project_id=project_id))


@bp.route("/update_cost_estimation/<int:project_id>", methods=["POST"])
@login_required
def update_cost_estimation(project_id):
    def normalize_float(value, default=0.0):
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return default

    try:
        project = Project.query.get_or_404(project_id)
        cost_estimation = project.cost_estimations.first()
        
        if cost_estimation:
            awg_total = 0.0
            conduit_total = 0.0
            
            # Update entries with normalized values
            for entry in cost_estimation.entries:
                if entry.type == 'AWG':
                    entry.cost = normalize_float(request.form.get(f'awg_cost_{entry.id}'))
                    entry.length = int(request.form.get(f'awg_length_{entry.id}', 0))
                    entry.subtotal = normalize_float(entry.cost * entry.length)
                    awg_total += entry.subtotal
                elif entry.type == 'Conduit':
                    entry.cost = normalize_float(request.form.get(f'conduit_cost_{entry.id}'))
                    entry.length = int(request.form.get(f'conduit_length_{entry.id}', 0))
                    entry.subtotal = normalize_float(entry.cost * entry.length)
                    conduit_total += entry.subtotal
            
            # Update tax and totals
            tax_percentage = normalize_float(request.form.get('tax_percentage'))
            subtotal = normalize_float(awg_total + conduit_total)
            tax_amount = normalize_float(subtotal * (tax_percentage / 100))
            grand_total = normalize_float(subtotal + tax_amount)
            
            cost_estimation.tax_percentage = tax_percentage
            cost_estimation.awg_total = awg_total
            cost_estimation.conduit_total = conduit_total
            cost_estimation.tax_amount = tax_amount
            cost_estimation.grand_total = grand_total
            
            db.session.commit()
            flash('Cost estimation updated successfully!', 'success')
        
        return redirect(url_for('portfolio.project_review', project_id=project_id))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating cost estimation: {str(e)}")
        flash('Error updating cost estimation', 'danger')
        return redirect(url_for('portfolio.project_review', project_id=project_id))
    

@bp.route("/update_misc_equipment/<int:project_id>", methods=["POST"])
@login_required
def update_misc_equipment(project_id):
    def normalize_float(value, default=0.0):
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return default

    try:
        project = Project.query.get_or_404(project_id)
        misc_equip = project.misc_equipment_estimations.first()
        
        if misc_equip:
            misc_total = 0.0
            equipment_total = 0.0
            
            # Update Miscellaneous entries
            for entry in misc_equip.entries:
                if entry.type == 'Miscellaneous':
                    entry.cost = normalize_float(request.form.get(f'misc_cost_{entry.id}'))
                    entry.quantity = int(request.form.get(f'misc_quantity_{entry.id}', 0))
                    entry.subtotal = normalize_float(entry.cost * entry.quantity)
                    misc_total += entry.subtotal
                elif entry.type == 'Equipment':
                    entry.cost = normalize_float(request.form.get(f'equipment_cost_{entry.id}'))
                    entry.quantity = int(request.form.get(f'equipment_quantity_{entry.id}', 0))
                    entry.subtotal = normalize_float(entry.cost * entry.quantity)
                    equipment_total += entry.subtotal
            
            # Update tax and totals
            tax_percentage = normalize_float(request.form.get('tax_percentage'))
            subtotal = normalize_float(misc_total + equipment_total)
            tax_amount = normalize_float(subtotal * (tax_percentage / 100))
            grand_total = normalize_float(subtotal + tax_amount)
            
            misc_equip.misc_total = misc_total
            misc_equip.equipment_total = equipment_total
            misc_equip.tax_percentage = tax_percentage
            misc_equip.tax_amount = tax_amount
            misc_equip.grand_total = grand_total
            
            db.session.commit()
            flash('Miscellaneous & Equipment updated successfully!', 'success')
        
        return redirect(url_for('portfolio.project_review', project_id=project_id))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating misc/equipment: {str(e)}")
        flash('Error updating miscellaneous & equipment', 'danger')
        return redirect(url_for('portfolio.project_review', project_id=project_id))
    

@bp.route("/update_labor_cost/<int:project_id>", methods=["POST"])
@login_required
def update_labor_cost(project_id):
    def normalize_float(value, default=0.0):
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return default

    try:
        project = Project.query.get_or_404(project_id)
        labor_cost = project.labor_cost_estimations.first()
        
        if labor_cost:
            labor_total = 0.0
            
            # Update labor entries with normalized values
            for entry in labor_cost.entries:
                entry.rate = normalize_float(request.form.get(f'rate_{entry.id}'))
                entry.workers = int(request.form.get(f'workers_{entry.id}', 0))
                entry.hours = normalize_float(request.form.get(f'hours_{entry.id}'))
                entry.days = normalize_float(request.form.get(f'days_{entry.id}'))
                entry.subtotal = normalize_float(entry.rate * entry.workers * entry.hours * entry.days)
                labor_total += entry.subtotal
            
            # Update charger information
            labor_cost.chargers_count = int(request.form.get('chargers_count', 0))
            labor_cost.charger_price = normalize_float(request.form.get('charger_price', 0))
            
            # Calculate low voltage total (consistent with frontend calculation)
            low_voltage_total = normalize_float(labor_cost.chargers_count * labor_cost.charger_price)
            
            # Calculate grand total
            labor_cost.labor_total = labor_total
            labor_cost.low_voltage_total = low_voltage_total
            labor_cost.grand_total = normalize_float(labor_total + low_voltage_total)
            
            db.session.commit()
            flash('Labor cost updated successfully!', 'success')
        
        return redirect(url_for('portfolio.project_review', project_id=project_id))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating labor cost: {str(e)}")
        flash('Error updating labor cost', 'danger')
        return redirect(url_for('portfolio.project_review', project_id=project_id))
    

@bp.route("/update_summary/<int:project_id>", methods=["POST"])
@login_required
def update_summary(project_id):
    def validate_positive_float(value, field_name, max_value=None):
        try:
            num = float(value)
            if num < 0:
                raise ValueError(f"{field_name} must be positive")
            if max_value is not None and num > max_value:
                raise ValueError(f"{field_name} must be ≤ {max_value}")
            return round(num, 2)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid {field_name}: must be a number")

    def validate_tax_percentage(value):
        return validate_positive_float(value, "Tax percentage", max_value=100)

    try:
        project = Project.query.get_or_404(project_id)
        summary = project.summaries.first()
        
        if not summary:
            flash('No project summary found', 'danger')
            return redirect(url_for('portfolio.project_review', project_id=project_id))

        # Update markups and percentages
        summary.awg_markup = validate_positive_float(request.form.get('awg_markup'), "AWG markup", min_value=1.0)
        summary.conduit_markup = validate_positive_float(request.form.get('conduit_markup'), "Conduit markup", min_value=1.0)
        summary.misc_markup = validate_positive_float(request.form.get('misc_markup'), "Misc markup", min_value=1.0)
        summary.equipment_markup = validate_positive_float(request.form.get('equipment_markup'), "Equipment markup", min_value=1.0)
        summary.labor_markup = validate_positive_float(request.form.get('labor_markup'), "Labor markup", min_value=1.0)
        summary.low_voltage_markup = validate_positive_float(request.form.get('low_voltage_markup'), "Low voltage markup", min_value=1.0)
        summary.permits_markup = validate_positive_float(request.form.get('permits_markup'), "Permits markup", min_value=1.0)
        
        summary.tax_percentage = validate_tax_percentage(request.form.get('tax_percentage'))
        summary.overhead_percentage = validate_positive_float(request.form.get('overhead_percentage'), "Overhead percentage")

        # Update approval status
        summary.approved = request.form.get('approved') == 'true'

        # Recalculate all values
        summary.awg_subtotal = round(summary.awg_base_cost * summary.awg_markup, 2)
        summary.awg_profit = round(summary.awg_subtotal - summary.awg_base_cost, 2)
        
        # Calculate all other categories similarly...
        
        # Calculate totals
        taxable_profit = (summary.awg_profit + summary.conduit_profit + summary.misc_profit + 
                         summary.equipment_profit + summary.labor_profit + summary.low_voltage_profit + 
                         summary.permits_profit)
        
        summary.tax_subtotal = round(taxable_profit * (summary.tax_percentage / 100), 2)
        
        grand_subtotal = (summary.awg_subtotal + summary.conduit_subtotal + summary.misc_subtotal + 
                         summary.equipment_subtotal + summary.labor_subtotal + summary.low_voltage_subtotal + 
                         summary.permits_subtotal)
        
        summary.overhead_subtotal = round(grand_subtotal * (summary.overhead_percentage / 100), 2)
        summary.grand_total = round(grand_subtotal + summary.tax_subtotal + summary.overhead_subtotal, 2)

        db.session.commit()
        flash('Project summary updated successfully!', 'success')
        
    except ValueError as e:
        db.session.rollback()
        flash(f'Validation error: {str(e)}', 'danger')
        current_app.logger.warning(f"Validation failed in summary update: {str(e)}")
    except Exception as e:
        db.session.rollback()
        flash('Error updating project summary', 'danger')
        current_app.logger.error(f"Error updating project summary: {str(e)}", exc_info=True)
    
    return redirect(url_for('portfolio.project_review', project_id=project_id))