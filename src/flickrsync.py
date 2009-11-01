import flickrapi
import pyexiv2
import os,sys,fnmatch
import hashlib

api_key = '3d910dbe5302ff28415039a78520debf'
api_secret = 'e0b09baf3bdd1945'

class FlickrSync:
    img_pattern = "*.jpg"
    flickr = False
    base_dir = False
    current_transfer_file  = False
    current_image_meta = False
    current_photo = False
    image_list = False
    iptc_keyword = "pyuploaded234"
    CONFIG_PATH = '.flickrsync'
    api_key = False
    api_secret = False
    
    def __init__(self, api_key, secret, img_dir):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_dir = img_dir
        
       
        
    def start(self):
        
        self.flickr = flickrapi.FlickrAPI(api_key, api_secret)
        (token, frob) = self.flickr.get_token_part_one(perms='write')
        if not token: raw_input("Press ENTER after you authorized this program")
        self.flickr.get_token_part_two((token, frob))
        
        self.setup_dir()
        self.image_list =  self.get_images_generator()
        self.process()
        
    def setup_dir(self):
        '''Setup configuration directory where we store which images 
        have been uploaded already.'''
        try:
            if not os.path.exists(os.path.join(self.base_dir, self.CONFIG_PATH)):
                os.mkdir(os.path.join(self.base_dir, self.CONFIG_PATH))
        except:
            print "Could not create configuration directory"
            sys.exit(1)

    def get_images_generator(self):
        '''Locate all files matching supplied filename pattern in and below
        supplied root directory.'''
        for path, dirs, files in os.walk(self.base_dir):
            for filename in fnmatch.filter(files, self.img_pattern):
                yield os.path.join(path, filename)
    
    def process(self):
        try:
            
            
            
            img = self.image_list.next()
            self.current_image_meta = pyexiv2.Image(img)
            self.current_image_meta.readMetadata()
            if "Iptc.Application2.Keywords" in self.current_image_meta.iptcKeys():
                keywords = list(self.current_image_meta["Iptc.Application2.Keywords"])
                if self.iptc_keyword in keywords:
                    self.process()
                else:
                    self.upload(img)
            else:
                self.upload(img)
        except StopIteration:
            pass
    
    def image_is_uploaded(self, img):
        
    
    def upload(self, file):
        image_tags = '"' + '" "'.join( file.replace(self.base_dir, '').split('/')[:-1] )+ '"'
        print image_tags
        self.current_transfer_file = file
        self.current_image_meta['Iptc.Application2.Keywords'] = 'uploaded'
        keywords = list(self.current_image_meta['Iptc.Application2.Keywords'])
        keywords.append(self.iptc_keyword)
        self.current_image_meta['Iptc.Application2.Keywords'] = keywords
        self.current_image_meta.writeMetadata()
        
        self.flickr.upload(filename=file, callback=self.cb, tags=image_tags)
        
    def cb(self, progress, done):
        if done:
            self.current_transfer_file = False
            print "Done uploading"
            self.process()
        else:
            print "At %s%%" % progress
            

class Photo:
    _hash = False
    path = False
    def __init(self, path):
        self.path = path
    
    def hash(self):
        if not self._hash:
            m = hashlib.md5()
            self._hash = m.update(open(self.path, 'rb').read()).hexdigest()
        return self._hash
    

try:
    f = FlickrSync(api_key, api_secret, '../images/')
    f.start()
except KeyboardInterrupt:
    sys.exit(0)
    
    
    