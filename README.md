Banners:
	* Banners should be resized to 1280x720
	* Banners should be compressed with JPEG (though we may be able to use HEIC)

Icons:
	* Icons should be resized to 250x250
	* Icons should be compressed with PNG

JSON:
	* Edit either the iPad or iPhone `-src` files first
	* iPad has 380 for FeaturedStackView 'preferredWidth'
	* iPhone has 400 for FeaturedStackView 'preferredWidth'
	* Use https://codebeautify.org/jsonminifier to generate the non `-src` files

For updating the featured page:
	* Create a fork/branch
	* Update the JSON and add banners/icons to the folders
	* Send a pull request