$(document).ready(function(){

	var flipkart_link = $(".flipkart_site_link").attr("href")

	$.ajax({
  		url: '/flip_delivery',
  		success: function(data)
  		{
  			$('.flipkart_delivery').html(data);
  			// alert("as")
  		}
	});

	var amazon_link = $(".amazon_site_link").attr("href")
	if(amazon_link == "#0")
	{
		$('.amazon_delivery').html("NA");
	}
	else
	{
		$.ajax({
	  		url: '/amazon_delivery',
	  		success: function(data)
	  		{
	  			$('.amazon_delivery').html(data);
	  			// alert("as")
	  		}
		});
	}


	var snapdeal_link = $(".snapdeal_site_link").attr("href")
	if(snapdeal_link == "#0")
	{
		$('.snapdeal_delivery').html("NA");
	}
	else
	{
		$.ajax({
	  		url: '/snapdeal_delivery',
	  		success: function(data)
	  		{
	  			$('.snapdeal_delivery').html(data);
	  			// alert("as")
	  		}
		});
	}


	var ebay_link = $(".ebay_site_link").attr("href")
	if(ebay_link == "#0")
	{
		$('.ebay_delivery').html("NA");
	}
	else
	{
		$.ajax({
	  		url: '/ebay_delivery',
	  		success: function(data)
	  		{
	  			$('.ebay_delivery').html(data);
	  			// alert("as")
	  		}
		});
	}

})