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

@app.route('/dashboard')
def table():
    df = pd.read_excel(os.path.dirname(os.path.realpath(__file__)) + '/scraper_overview.xlsx')
    return render_template('dashboard.html', df=df)

@app.route('/upload', methods=['POST'])
def upload():
   file = request.files['file']
   if file and file.filename.endswith('.xlsx'):
       file.save(os.path.dirname(os.path.realpath(__file__))+ '/scraper_overview.xlsx')
   return redirect(url_for('table'))

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    return send_from_directory(os.path.dirname(os.path.realpath(__file__)), filename)

@app.route('/pdf')
def show_pdf():
    return render_template('pdf.html', pdf_filename='information.pdf')

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')
