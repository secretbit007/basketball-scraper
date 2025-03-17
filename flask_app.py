from library import *

from euroleauge_eurocup import func_euroleague_eurocup
from nba_ncaa_g import func_nba_ncaa_g
from italy import func_italy_a1, func_italy_a2, func_italy_b
from spain import func_leboro, func_lebplata
from serbia import func_kls
from naia import func_naia
from cancis import func_cancis
from vtb import func_vtb
from kzs import func_kzs
from fiba import func_fiba
from nbl import func_nbl
from kos import func_kos
from cbffe import func_cbffe
from sbf import func_sbf
from ecbbl import func_ecbbl
from bnxt import func_bnxt
from blg import func_blg
from fpb import func_fpb
from ncaa import func_ncaa

app = Flask(__name__)

@app.route('/', methods=['GET'])
def get_data():
    args = {}
    args['f'] = request.args.get('f')
    args['lpar'] = request.args.get('lpar')
    args['source'] = request.args.get('source')
    args['season'] = request.args.get('season')
    args['extid'] = request.args.get('extid')

    if args['source'] == 'FIBA_Livesco':
        return func_blg(args)

    # Euroleague & Eurocup
    if args["lpar"] == 'E' or args["lpar"] == 'U':
        return func_euroleague_eurocup(args)
    # NBA & NCAA
    elif args["lpar"] == 'NBA' or args['lpar'] == 'G' or args['lpar'] == 'NCAA':
        return func_nba_ncaa_g(args)
    # Italy Season A & A2
    elif args["lpar"] == 'SerieA1':
        return func_italy_a1(args)
    elif args["lpar"] == 'SerieA2':
        return func_italy_a2(args)
    elif args["lpar"] == 'SerieB':
        return func_italy_b(args)
    elif args["lpar"] == 'LEBORO':
        return func_leboro(args)
    elif args["lpar"] == 'LEBPLATA':
        return func_lebplata(args)
    elif args["lpar"] == 'KLS':
        return func_kls(args)
    elif args["lpar"] == "NAIA":
        return func_naia(args)
    elif args["lpar"] == "CANCIS":
        return func_cancis(args)
    elif args["lpar"] == "VTB":
        return func_vtb(args)
    elif args["lpar"] == 'KZS':
        return func_kzs(args)
    elif args["lpar"] == "FUBB":
        return func_fiba(args)
    elif args['lpar'] == "BIH":
        return func_fiba(args)
    elif args['lpar'] == "NBL":
        return func_nbl(args)
    elif args['lpar'] == "ESAKE":
        return func_fiba(args)
    elif args['lpar'] == "KOS":
        return func_kos(args)
    elif args['lpar'] == "CBFFE":
        return func_cbffe(args)
    elif args['lpar'] == "SBF":
        return func_sbf(args)
    elif args['lpar'] == "ECBBL":
        return func_ecbbl(args)
    elif args['lpar'] == 'BNXT':
        return func_bnxt(args)
    elif args['lpar'] == 'FPB':
        return func_fpb(args)
    elif args['lpar'] == 'NCAAD3':
        return func_ncaa(args, 'D-III')
    elif args['lpar'] == 'NCAAD2':
        return func_ncaa(args, 'D-II')

    return {'error': 'Something went wrong!'}

EXCEL_PATH = '/home/BasketballDatabase/mysite/scraper_overview.xlsx'

# HTML Template with DataTables and upload form
template = """
<!doctype html>
<html lang="en">
 <head>
   <meta charset="utf-8">
   <meta name="viewport" content="width=device-width, initial-scale=1">
   <title>Scraper Overview</title>
   <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
   <style>
     body { font-family: Arial, sans-serif; margin: 20px; }
     .upload-form { margin-bottom: 20px; }
     .filter-select { width: 100%; box-sizing: border-box; } /* Style for filter dropdowns */
   </style>
 </head>
 <body>
   <h1>Scraper Overview Table</h1>

   <div class="upload-form">
     <form action="/upload" method="POST" enctype="multipart/form-data">
       <label>Upload updated Excel:</label>
       <input type="file" name="file" accept=".xlsx" required>
       <button type="submit">Upload</button>
     </form>
   </div>

   <table id="scraperTable" class="display">
     <thead>
       <tr>
         {% for col in df.columns %}
           <th>{{ col }}</th>
         {% endfor %}
       </tr>
       <tr class="filters"> <!-- Row for filter dropdowns -->
         {% for col in df.columns %}
           <th>
             <select class="filter-select" data-column="{{ loop.index0 }}">
               <option value="">All</option> <!-- Default option to show all -->
               {% for value in df[col].unique() %}
                 <option value="{{ value }}">{{ value }}</option>
               {% endfor %}
             </select>
           </th>
         {% endfor %}
       </tr>
     </thead>
     <tbody>
       {% for row in df.itertuples(index=False) %}
       <tr>
         {% for value in row %}
           <td>{{ value }}</td>
         {% endfor %}
       </tr>
       {% endfor %}
     </tbody>
   </table>

   <script src="https://code.jquery.com/jquery-3.5.1.js"></script>
   <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
   <script>
     $(document).ready(function() {
       var table = $('#scraperTable').DataTable({
         paging: true,
         searching: true,
         ordering: true
       });

       // Add filter dropdowns to the header
       $('.filter-select').on('change', function() {
         var columnIndex = $(this).data('column'); // Get column index
         var filterValue = this.value; // Get selected value
         table.column(columnIndex).search(filterValue).draw(); // Apply filter
       });
     });
   </script>
 </body>
</html>
"""

@app.route('/dashboard')
def table():
    df = pd.read_excel(EXCEL_PATH)
    return render_template_string(template, df=df)

@app.route('/upload', methods=['POST'])
def upload():
   file = request.files['file']
   if file and file.filename.endswith('.xlsx'):
       file.save(EXCEL_PATH)
   return redirect(url_for('table'))

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    return send_from_directory('/home/BasketballDatabase/mysite', filename)

@app.route('/pdf')
def show_pdf():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PDF Viewer</title>
        </head>
        <body>
            <iframe
                src="{{ url_for('serve_pdf', filename=pdf_filename) }}"
                width="100%"
                height="800px"
                style="border: none;">
            </iframe>
            <p>If the PDF does not display, <a href="{{ url_for('serve_pdf', filename=pdf_filename) }}">click here to download it</a>.</p>
        </body>
        </html>
    ''', pdf_filename='information.pdf')
